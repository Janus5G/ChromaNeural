# Architecture and scope

The unchanged desktop runs existing Settings and Participation, WorkQueue, explicit AI-provider selection, approved peer TLS/inbox and existing review/publication contracts. Source is retained at its original relative paths to preserve imports, provider subprocesses and runtime lookup. The packaging layer assembles dependencies and installers; it does not change job or owner semantics.

The Internet Computer application is a separate component and is not deployed by this repository workflow. Local acceptance of integrated app guards does not imply they are live. Browser Internet Identity remains external. Native owner-write bridging and private requester-result delivery remain outside this RC.

The official Linux amd64 DEB wraps the existing native launcher and Python process model. Portable code is retained for community ports; Windows, macOS and mobile platforms are not officially supported or verified. Unsupported worker/resource/compiler profiles remain fail-closed.
