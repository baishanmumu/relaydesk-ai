# RelayDesk browser workspace

FastAPI serves the chat page, session history, operation timeline, and user approval actions. The root [project README](../README.md) documents the standard Docker and local Poetry setup.

Session records are created under `user_data/` at runtime. This directory is ignored by Git; do not commit conversation data.
