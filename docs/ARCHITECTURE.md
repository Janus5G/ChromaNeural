# Architecture and scope

The unchanged desktop runs existing Settings and Participation, WorkQueue, explicit AI-provider selection, approved peer TLS/inbox and existing review/publication contracts. Source is retained at its original relative paths to preserve imports, provider subprocesses and runtime lookup. The packaging layer assembles dependencies and installers; it does not change job or owner semantics.

The Internet Computer application is a separate component and is not deployed by this repository workflow. Local acceptance of integrated app guards does not imply they are live. Browser Internet Identity remains external. Native owner-write bridging and private requester-result delivery remain outside this RC.

Windows packages retain the existing ordinary Python process model, so sys.executable continues to identify Python in subprocess flows. Linux DEB wraps the existing native launcher. RC4 packages support Windows x64 and Linux amd64 only. Unsupported worker/resource/compiler profiles remain fail-closed.
