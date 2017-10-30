import base64
import datetime
import json
import logging

import party

from ..credentials import load_credentials

LOG = logging.getLogger(__name__)

CREDENTIALS = load_credentials()

PARTY_CONFIG = {
    'artifactory_url': CREDENTIALS['artifactory_url'],
    'username': CREDENTIALS['artifactory_username'],
    'password': base64.encodebytes(bytes(CREDENTIALS['artifactory_password'], 'utf-8')),
}


class Artifactory(object):

    artifactory = party.Party(PARTY_CONFIG)

    @staticmethod
    def _parse_artifact_name(name):
        simple_name = '/'.join(name.split('/')[-4:])
        return simple_name

    def list(self, repo_name=None):
        """
        Return a list of repos with basic info about each
        If the optional parameter repo_name is specified, then only return
        information pertaining to that repo
        """

        repos = {}

        raw_data = self.artifactory.request('storageinfo')
        data = raw_data.json()
        for repo in data["repositoriesSummaryList"]:
            if repo["repoKey"] == "TOTAL":
                continue

            if not repo_name or repo_name == repo["repoKey"]:
                repos[repo["repoKey"]] = repo

        return repos

    def all_artifacts(self, search='', repo='', depth=3):
        """ Returns a dict of artifact and properties """
        LOG.debug('Finding all artifacts with: search=%s, repo=%s, depth=%s', search, repo, depth)
        all_artifacts = {}

        self.artifactory.find_by_pattern(filename=search, specific_repo=repo, max_depth=depth)

        for artifact in sorted(self.artifactory.files):
            artifact_simple_name = self._parse_artifact_name(artifact)
            LOG.debug('Found: %s', artifact_simple_name)
            self.artifactory.get_properties(artifact)

        LOG.info('Found %d artifacts in total.', len(all_artifacts))
        return all_artifacts

    def purge(self, repo, dry_run, artifacts):
        """ Purge artifacts from the specified repo

        Keyword arguments:
        repo -- the repo to target for this operation
        dry_run -- false to execute an actual purge
        artifacts -- a list of artifacts to operate upon
        """
        purged = 0
        mode = "DRYRUN" if dry_run else "LIVE"

        for artifact in artifacts:
            LOG.info("  {} purge {}:{}".format(mode, repo, artifact))
            if dry_run:
                purged += 1
            else:
                try:
                    self.artifactory.request(artifact, method='delete')
                    purged += 1
                except Exception as e:
                    LOG.error(str(e))

        return purged

    def filter(self, repo, terms=None, depth=3, sort=None, offset=None, limit=None):
        """Get a subset of artifacts from the specified repo.

        XXX: this looks at the project level, but actually need to iterate lower at project level
        XXX: almost certainly needs to set depth parameter to get to specific build

        Keyword arguments:
        repo -- the repo to target for this operation
        terms -- an array of jql snippets that will be ANDed together
        depth -- how far down the folder hierarchy to look
        offset -- how many items from the beginning of the list should be skipped (optional)
        limit -- the maximum number of entries to return (optional)

        This method does not use pagination. It assumes that this utility
        will be called on a repo sufficiently frequently that removing just
        the default n items will be enough.
        """

        if terms is None:
            terms = []

        terms.append({"repo": {"$eq": repo}})
        terms.append({"type": {"$eq": "folder"}})
        terms.append({"depth": {"$eq": depth}})

        find_expr = json.dumps({"$and": terms})

        aql = "items.find({})".format(find_expr)

        if sort:
            aql += ".sort({})".format(json.dumps(sort))

        if offset:
            aql += ".offset({})".format(offset)

        if limit:
            aql += ".limit({})".format(limit)

        LOG.debug("AQL: {}".format(aql))

        response = self.artifactory.find_by_aql(criteria=aql)

        return response["results"]

    def retain(self, repo, spec_project, depth, terms=None, count=None, weeks=None):
        if [terms, count, weeks].count(None) != 2:
            raise ValueError("Must specify exactly one of terms, count, or weeks")

        purgable = []

        for project in self.filter(repo, depth=depth):
            if spec_project and spec_project != project["name"]:
                continue

            path = "{}/{}".format(project["path"], project["name"])
            if count:
                for artifact in self.filter(
                        repo, offset=count, depth=depth + 1, terms=[{
                            "path": path
                        }], sort={"$desc": ["created"]}):
                    purgable.append("{}/{}".format(artifact["path"], artifact["name"]))

            if weeks:
                now = datetime.datetime.now()
                before = now - datetime.timedelta(weeks=weeks)
                created = before.strftime("%Y-%m-%dT%H:%M:%SZ")

                for artifact in self.filter(
                        repo, offset=count, depth=depth + 1, terms=[{
                            "path": path
                        }, {
                            "created": created
                        }]):
                    purgable.append("{}/{}".format(artifact["path"], artifact["name"]))

            if terms:
                pass

        return purgable
