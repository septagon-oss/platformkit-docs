# Working in this repository

1. A page links to the source of truth and states nothing the source does not.
   If a fact is not in `septagon-oss/platformkit` (or `platformkit-mobile`),
   it does not belong here.
2. One page per concept, in `docs/modules/ROOT/pages/`; add it to `nav.adoc`.
3. `make check` passes before you commit. It fails on any Antora warning.
4. Commands, paths and identifiers are copied exactly from the repository they
   describe. Version numbers come from `docs/antora.yml` attributes, never from
   prose.
5. No generated content, no copied files from the source repository except
   `images/logo.png`, the architecture maps under `attachments/`, which are
   copied from `ops/platformkit-record/architecture/` in the workspace, and
   the three tables on every feature page between `// generated:…` markers.
   `make tables` renders those from `scripts/openapi.json`, the document the
   application serves at `/openapi.json` with `server.docs` on, and from the
   module manifests; refresh the snapshot and `scripts/openapi.revision`
   together, and never edit inside the markers.
6. A feature page is `pages/features/<module>.adoc` from `templates/feature.adoc`
   and a decision page is `pages/decisions/<NNNN>-<slug>.adoc` from
   `templates/decision.adoc`: same headings, same order, the map first. The
   map is delivered from the matching template in the programme record and
   copied to `attachments/features/` or `attachments/decisions/`; add the page
   to `nav.adoc` and to the index page.
