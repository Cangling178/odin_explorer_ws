# ODIN1 vendor underlay

English | [Chinese](README_cn.md)

Reserved for `src/odin_ros_driver` from the vendor repository. Vendor sources,
SDK binaries and underlay build products are ignored in the parent Git repository.
`COLCON_IGNORE` prevents accidental root-level discovery. The first-party build
uses `--base-paths src` at the root, not this directory.

Before importing: check the exact release/firmware pair and review the build
script. Keep the vendor package directly under this underlay's `src/` directory
because the vendor documents layout assumptions. Use the audited vendor build
procedure within this directory; the first-party foundation does not invoke it.

After a successful import/build, record commit SHA, license, SDK provenance,
firmware, local patches and a smoke-test report. Source this underlay before
the first-party overlay. See `docs/04_odin1_integration.md` for acceptance.
No vendor driver is installed by the foundation.
