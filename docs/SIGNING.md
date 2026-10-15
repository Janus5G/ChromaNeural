# Code signing policy

Official RC5 distribution is Linux amd64 only. SignPath, Inno Setup and Authenticode are not active release requirements. No Windows executable is distributed. The following record preserves earlier Windows TEST evidence and deferred production work; it is historical, not an instruction to run the current workflow or a blocker for Linux.

## Historical Windows state

Separate SignPath TEST request, Authenticode signature presence, expected certificate and signed-artifact hash correlation: PASS according to the owner-provided Windows/SignPath evidence. This is not integrated CI signing or trusted production signing.

Signer subject (exact spelling): `CN=ChromaNeural Test signing`, `O=Chromanural`, `OU=Developement`, `C=DK`. Final TEST-signed artifact SHA-256: `87FA5581F795EBA504361DBFB91335851770661644B965BAB76BFF0DA57E6D00`, confirmed by the owner to match SignPath. Windows reported `UnknownError`, attributed in that evidence specifically to an untrusted self-signed root. This does not generally make `UnknownError` acceptable and does not establish public trust.

SIGNPATH CI INTEGRATION = BLOCKED — TRUSTED BUILD SYSTEM NOT AVAILABLE. The successful Windows/Linux CI run skipped its signing job. Trusted Build System and origin verification have not passed; no security boundary was bypassed.

The existing ChromaNeural project, PE artifact configuration, CI submitter, self-signed test certificate and TEST policy must be reused. Display names are not configuration slugs. The separate TEST result does not establish the GitHub secret/variable bindings or certificate fingerprint required by the integrated workflow; those bindings remain NOT VERIFIED here. No token value is recorded in this documentation.

## Historical integrated Windows CI prerequisites

These are conditional prerequisites for the blocked integrated job, not instructions to repeat the completed separate TEST request.

1. In the existing SignPath organization, open the ChromaNeural project and existing TEST signing policy. Copy the exact organization ID, project slug, PE artifact configuration slug and test-policy slug from their details. Record the SHA-256 fingerprint of the actual test certificate's DER bytes. Do not create duplicates or infer slugs from names.
2. In GitHub: repository **Settings → Secrets and variables → Actions → New repository secret**. Name it `SIGNPATH_API_TOKEN`; enter the existing CI token privately and save. Never paste it into an issue, source file or conversation. Its existence has not been verified here.
3. Add repository/environment variables `SIGNPATH_ORGANIZATION_ID`, `SIGNPATH_PROJECT_SLUG`, `SIGNPATH_ARTIFACT_CONFIGURATION_SLUG`, `SIGNPATH_TEST_POLICY_SLUG`, `SIGNPATH_TEST_CERT_SHA256` with those verified non-secret values. Restrict the `rc5-signing-test` environment to an approved branch and owner review. No production policy is selected by this workflow.
4. In SignPath Organization → Trusted Build Systems, reuse/add the predefined **GitHub.com** system and link it to the existing project. Confirm the repository URL is exactly `https://github.com/Janus5G/ChromaNeural`. Install/authorize the SignPath GitHub App for this repository if required for audit-log evaluation. These account/security changes require owner action and are BLOCKED here.
5. In the existing policy, review trusted-build-system verification and **Verify origin**, including allowed branch names/source-review requirements. Do not disable verification to make a request pass. Their current account state is NOT VERIFIED.
6. Only after Trusted Build System/origin verification and the exact account bindings are established, and a separate owner authorization permits the run, dispatch the RC5 workflow with `test_sign=true`. It builds from clean GitHub-hosted checkout, validates the unsigned installer, uploads a raw PE for the existing PE configuration, requests test signing, then checks the returned certificate/signature and hashes the signed bytes. It never creates a public release.

A test certificate is not a trusted public certificate. The verifier accepts only the explicitly bound self-signed RSA-4096 code-signing certificate with Windows status Valid or NotTrusted, and records the actual trust result. HashMismatch, unsigned and other errors fail, including the reported `UnknownError`. Therefore the separate owner-verified test is not a PASS for this unexecuted CI verifier. No trust-store changes are made.

## Production signing

SignPath Foundation acceptance and production certificate: BLOCKED — EXTERNAL SIGNPATH RESPONSE PENDING. The completed scoped license inventory found Apache-2.0/MIT project runtime, unchanged third-party licenses and restrictive PRISME/Binary Extension material only as historical/provenance notices, not a restrictive runtime component. Foundation acceptance of the Inno Setup-generated installer remains NOT VERIFIED pending external confirmation. No license is changed or Foundation approval claimed. Do not purchase a certificate or submit an application without owner authorization.

The former Windows release plan required trusted production signing, signed-artifact verification and owner manual acceptance; that requirement does not apply to the Linux-only official release. This workflow's test artifact must never be labelled trusted release signing.

## Authoritative references

- [Official GitHub integration](https://docs.signpath.io/trusted-build-systems/github)
- [Origin verification](https://docs.signpath.io/origin-verification/)
- [Foundation terms](https://signpath.org/terms.html)
- [Current Inno Setup downloads](https://jrsoftware.org/isdl.php)

The pinned upload action uses `archive: false`, because the existing artifact type is PE, not ZIP. SignPath uses `skip-decompress: true`. This avoids creating a duplicate artifact configuration merely for CI.
