# platformkit-docs

The documentation site for [PlatformKit](https://github.com/septagon-oss/platformkit),
published at https://septagon-oss.github.io/platformkit-docs.

It is deliberately thin. `ARCHITECTURE.md`, the ADRs, `CONTRIBUTING.md` and the
package comments in the source repository are the truth; the pages here are the
narrative that gets a reader to the right file, and they link to it rather than
copy it. The previous site copied, described a 0.x world for weeks after that
world was archived, and could not be corrected because its repository was
read-only. This one says less and cannot drift as far.

    npm ci
    make check     # builds with Antora; a warning is a failure
    make serve     # http://localhost:5000

Pages are AsciiDoc under `docs/modules/ROOT/pages/`; navigation is
`docs/modules/ROOT/nav.adoc`. One component, one version (`v1.0`). The site is
built and deployed to GitHub Pages by `.github/workflows/docs.yml` on every
push to `main`.
