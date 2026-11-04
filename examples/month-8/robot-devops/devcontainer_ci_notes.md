# Dev Container + action-ros-ci (student repo only)

These templates are for **your** hardware-component or policy repo. They do not run inside the Hardware-learning site CI.

## Dev Container (ROS 2 Jazzy)
Official guide: *Setup ROS 2 with VSCode and Docker* (ros2_documentation jazzy:
`How-To-Guides/Setup-ROS-2-with-VSCode-and-Docker-Container.rst`).

Layout:

```
your_ws/
├── .devcontainer/
│   ├── devcontainer.json
│   └── Dockerfile
└── src/
```

Install VS Code + Docker, then the Remote Development extension, open `your_ws`, and reopen in container.

## GitHub Actions + action-ros-ci
`ros-tooling/action-ros-ci` runs `colcon build` and `colcon test` (tests can be skipped). Prefer pinning a released tag (see upstream README). Example sketch:

```yaml
# .github/workflows/ros-ci.yaml  (in YOUR repo)
jobs:
  build-and-test:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
      - uses: ros-tooling/setup-ros@v0.7
        with:
          required-ros-distributions: jazzy
      - uses: ros-tooling/action-ros-ci@v0.4
        with:
          package-name: your_package
          target-ros2-distro: jazzy
```

## rosbag2 default format on Jazzy
On the `jazzy` branch of `ros2/rosbag2`, `rosbag2_storage::get_default_storage_id()` returns `"mcap"`. Iron’s release notes first switched the default writer to MCAP; Jazzy keeps that default (sqlite3 remains available for playback/write if selected).
