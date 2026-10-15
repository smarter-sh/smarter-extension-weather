/**
 * semantic-release, run by .github/workflows/release.yml on each push to main.
 *
 * It reads the conventional commits since the last v* tag: a fix releases a patch, a feat a minor
 * version, and a BREAKING CHANGE a major version. Then it:
 *
 * 1. adds the release's notes to CHANGELOG.md;
 * 2. sets the version in pyproject.toml, and builds the archive, dist/<slug>-<version>.zip, and its
 *    sha256, dist/<slug>-<version>.zip.sha256 (scripts/set_version.py, scripts/package.py);
 * 3. commits CHANGELOG.md and pyproject.toml, and tags the commit v<version>;
 * 4. creates the GitHub release, with the archive and its sha256 attached.
 *
 * The release's entry in smarter-sh/extensions-registry, extensions/<slug>/<version>.yaml, needs
 * the archive's url and sha256, which the workflow's summary prints.
 */
module.exports = {
  branches: ["main"],
  tagFormat: "v${version}",
  plugins: [
    [
      "@semantic-release/commit-analyzer",
      {
        preset: "conventionalcommits",
        releaseRules: [
          { type: "docs", release: false },
          { type: "test", release: false },
          { type: "style", release: false },
          { type: "refactor", release: false },
        ],
        parserOpts: {
          noteKeywords: ["BREAKING CHANGE", "BREAKING CHANGES"],
        },
      },
    ],
    [
      "@semantic-release/release-notes-generator",
      {
        preset: "conventionalcommits",
        presetConfig: {
          types: [
            { type: "feat", section: "Features", hidden: false },
            { type: "fix", section: "Bug Fixes", hidden: false },
            { type: "refactor", section: "Refactoring", hidden: false },
            { type: "perf", section: "Performance", hidden: false },
          ],
        },
      },
    ],
    // before the build, so that the archive's CHANGELOG.md has this release's notes.
    ["@semantic-release/changelog", { changelogFile: "CHANGELOG.md", changelogTitle: "# Changelog" }],
    [
      "@semantic-release/exec",
      {
        prepareCmd: "python scripts/set_version.py ${nextRelease.version} && python scripts/package.py dist",
      },
    ],
    [
      "@semantic-release/git",
      {
        assets: ["CHANGELOG.md", "pyproject.toml"],
        message: "chore(release): ${nextRelease.version} [skip ci]\n\n${nextRelease.notes}",
      },
    ],
    [
      "@semantic-release/github",
      {
        assets: ["dist/*.zip", "dist/*.zip.sha256"],
        successComment: false,
        failComment: false,
        releasedLabels: false,
      },
    ],
  ],
};
