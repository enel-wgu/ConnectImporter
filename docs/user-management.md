# User management and identity sources

Amazon Connect user identity is split into two separate concerns in this project:

- `UserIdentity` carries portable identity data such as first name, last name, email, secondary email, and mobile. This is a data model, not a Terraform-managed resource.
- `ConnectUserConfig` contains the Connect-side configuration Terraform manages: routing profile, security profiles, and hierarchy group.

The source instance's `identity_management_type` determines what Terraform is allowed to emit. For SAML-managed instances, the generator omits `email` because the Connect API rejects it. For EXISTING_DIRECTORY users, the generator sets `directory_user_id = var.directory_user_id_*`. For CONNECT_MANAGED users, the generator sets `password = var.user_password_*`.

This project does not attempt to recreate external identity providers in Terraform. AD/SAML identity is an external dependency that must exist on the target instance before the Connect-side association is applied.
