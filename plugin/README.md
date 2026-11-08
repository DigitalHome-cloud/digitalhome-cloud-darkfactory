# dhc

DigitalHome.Cloud's own agent skills, in one plugin. They live here, in the
umbrella repository, because they span the apps it checks out under `repos/`:

- **`dhc-amplify-gen2`:** the shared Amplify Gen 2 backend in `repos/core`.
- **`design-implement`:** implementing a Claude Design handoff in a real app.
- **`dhc-ontology-explorer`:** the T-Box, and the curator flow that promotes
  terms into it.
- **`dhc-build-blockly-elements-for-spatial-modeling`,
  `dhc-electrical-installation-design` and `dhc-blockly-sync-examples`:** the
  Designer's Blockly design views, generated from the T-Box.
- **`dhc-floorplan-demo`:** the floor-plan demo.
- **`dhc-device-autodiscovery`:** discovering a site's devices into the
  catalogue.

The security audit is not here. It is `dlab5-security-audit` in the
`dlab5-house` plugin, for every D-LAB-5 domain; its Amplify and edge modules
came from DHC.

**Install** from the D-LAB-5 catalogue:

```
/plugin marketplace add d-lab-5/agent-skills
/plugin install dhc@d-lab-5
```

**Change a skill** here, in its one home, then bump `version` in
`.claude-plugin/plugin.json`. Try a working copy with
`claude --plugin-dir plugin`. Never copy a skill into an app repository; the
repository's `.claude/settings.json` enables the plugin instead.

The skills are MIT-licensed (`LICENSE`), like most DigitalHome.Cloud
repositories.
