# Code signing policy - RC5

## Current state

TEST SignPath integration: BLOCKED until the existing account identifiers and certificate fingerprint can be verified and the owner authorizes the GitHub workflow. No signing request has been made. No token file was read. No certificate or policy was recreated.

The owner reports an existing ChromaNeural project, PE artifact configuration, ChromaNeural-GitHub-Actions CI submitter, RSA-4096 self-signed test certificate and test policy. Display names are not configuration slugs. The existing account was not accessible through the available browser connection; these exact account values remain NOT VERIFIED.

## Owner account configuration

1. In the existing SignPath organization, open the ChromaNeural project and existing TEST signing policy. Copy the exact organization ID, project slug, PE artifact configuration slug and test-policy slug from their details. Record the SHA-256 fingerprint of the actual test certificate's DER bytes. Do not create duplicates or infer slugs from names.
2. In GitHub: repository **Settings → Secrets and variables → Actions → New repository secret**. Name it `SIGNPATH_API_TOKEN`; enter the existing CI token privately and save. Never paste it into an issue, source file or conversation. Its existence has not been verified here.
3. Add repository/environment variables `SIGNPATH_ORGANIZATION_ID`, `SIGNPATH_PROJECT_SLUG`, `SIGNPATH_ARTIFACT_CONFIGURATION_SLUG`, `SIGNPATH_TEST_POLICY_SLUG`, `SIGNPATH_TEST_CERT_SHA256` with those verified non-secret values. Restrict the `rc5-signing-test` environment to an approved branch and owner review. No production policy is selected by this workflow.
4. In SignPath Organization → Trusted Build Systems, reuse/add the predefined **GitHub.com** system and link it to the existing project. Confirm the repository URL is exactly `https://github.com/Janus5G/ChromaNeural`. Install/authorize the SignPath GitHub App for this repository if required for audit-log evaluation. These account/security changes require owner action and are BLOCKED here.
5. In the existing policy, review trusted-build-system verification and **Verify origin**, including allowed branch names/source-review requirements. Do not disable verification to make a request pass. Their current account state is NOT VERIFIED.
6. After source review and authorized push, dispatch the RC5 workflow with `test_sign=true`. It builds from clean GitHub-hosted checkout, validates the unsigned installer, uploads a raw PE for the existing PE configuration, requests test signing, then checks the returned certificate/signature and hashes the signed bytes. It never creates a public release.

A test certificate is not a trusted public certificate. The verifier accepts only the explicitly bound self-signed RSA-4096 code-signing certificate with Windows status Valid or NotTrusted, and records the actual trust result. HashMismatch, unsigned and other errors fail. No trust-store changes are made.

## Production signing

SignPath Foundation acceptance and production certificate: BLOCKED / NOT VERIFIED. The Apache root license is insufficient evidence of eligibility. Actual payload terms include MIT/Apache dependencies and separate restrictive PRISME notices; whether excluded reference terms affect eligibility requires a Foundation decision over the exact payload. No license is changed or eligibility claimed. Do not purchase a certificate or submit an application without owner authorization.

Public RC5 release additionally requires trusted production signing, signed-artifact verification and owner manual acceptance. This workflow's test artifact must never be labelled trusted release signing.

## Authoritative references

- [Official GitHub integration](https://docs.signpath.io/trusted-build-systems/github)
- [Origin verification](https://docs.signpath.io/origin-verification/)
- [Foundation terms](https://signpath.org/terms.html)
- [Current Inno Setup downloads](https://jrsoftware.org/isdl.php)

The pinned upload action uses `archive: false`, because the existing artifact type is PE, not ZIP. SignPath uses `skip-decompress: true`. This avoids creating a duplicate artifact configuration merely for CI.
