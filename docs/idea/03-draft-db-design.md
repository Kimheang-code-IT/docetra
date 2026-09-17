## DB


### `role`
- `id [uuid]`: use as `primary key`
- `created_at [timestamp with time zone]`: by default is `now()`
- `updated_at [timestamp with time zone]`: by default is `now()`
- `created_by [uuid]`: the fkey, reference `officer.id`
- `updated_by [uuid]`: the fkey, reference `officer.id`
- `nam [character varying]`: for the name
- `lvl [int]`: `0` for the top 1 (only for super-admin), by default is `1` as value
- `description [text]`: describe the thing
- `is_active [smallint]`: by default it's `0`


### menu
- `id [uuid]`: use as `primary key`
- `created_at [timestamp with time zone]`: by default is `now()`
- `updated_at [timestamp with time zone]`: by default is `now()`
- `created_by [uuid]`: the fkey, reference `officer.id`
- `updated_by [uuid]`: the fkey, reference `officer.id`
- `parent_code [character varying]`: for self-join on `code`
- `code [character varying]`: it's `UNIQUE`
- `title [character varying]`: store as `translation-key` for use to translate in code
- `icon [character varying]`: store `icon-text` for convert to object in code
- `ordering [int]`: ordering
- `is_menu [smallint]`: 1 for item in navigation, 0 for action (create, edit, delete...)


## permission
- `id [uuid]`: use as `primary key`
- `created_at [timestamp with time zone]`: by default is `now()`
- `updated_at [timestamp with time zone]`: by default is `now()`
- `created_by [uuid]`: the fkey, reference `officer.id`
- `updated_by [uuid]`: the fkey, reference `officer.id`
- `role_id [uuid]`: the fkey, reference `role.id`
- `code [character varying]`: for join `menu.code`
- `is_enable [smallint]`: by default is `0`, while `0` for not allow and `1` is allow


## organization
- `id [uuid]`: use as `primary key`
- `created_at [timestamp with time zone]`: by default is `now()`
- `updated_at [timestamp with time zone]`: by default is `now()`
- `created_by [uuid]`: the fkey, reference `officer.id`
- `updated_by [uuid]`: the fkey, reference `officer.id`
- `nam [character varying]`: by default it's empty
- `lvl [bigint]`: by default it's `1`
- `description [text]`: info
- `is_active [smallint]`: by default it's `0`, while `0` is inactive, `1` is active
- `parent_id [uuid]`: for self-join on `id`
- `sector_id [uuid]`: the fkey, reference `organization_sector.id`
- `tax_id [character varying]`: for tax id, free text
- `organization_type [character varying]`: it's enum, `[company, government]`
- `address [text]`: for address, free text
- `contact_info [text]`: for contact info, free text
- `email [character varying]`: for email
- `phone [character varying]`: for phone
- `organization_purpose_id [uuid]`: the fkey, reference `organization_purpose.id`
- `logo_url [character varying]`: to store url
- `child_ids [text]`: for store child id(s), store `organization.id` in text, separated by comma


## organization_sector
- `id [uuid]`: use as `primary key`
- `created_at [timestamp with time zone]`: by default is `now()`
- `updated_at [timestamp with time zone]`: by default is `now()`
- `created_by [uuid]`: the fkey, reference `officer.id`
- `updated_by [uuid]`: the fkey, reference `officer.id`
- `nam [character varying]`: by default it's empty
- `parent_id [uuid]`: for self-join on `id`, reference `organization_sector.id`
- `description [text]`: info
- `is_active [smallint]`: by default it's `0`, while `0` is inactive, `1` is active


## organization_purpose
- `id [uuid]`: use as `primary key`
- `created_at [timestamp with time zone]`: by default is `now()`
- `updated_at [timestamp with time zone]`: by default is `now()`
- `created_by [uuid]`: the fkey, reference `officer.id`
- `updated_by [uuid]`: the fkey, reference `officer.id`
- `nam [character varying]`: by default it's empty
- `is_active [smallint]`: by default it's `0`, while `0` is inactive, `1` is active
- `description [text]`: info


## officer
- `id [uuid]`: use as `primary key`
- `created_at [timestamp with time zone]`: by default is `now()`
- `updated_at [timestamp with time zone]`: by default is `now()`
- `created_by [uuid]`: the fkey, reference `officer.id`
- `updated_by [uuid]`: the fkey, reference `officer.id`
- `nam [character varying]`: by default it's empty
- `is_active [smallint]`: by default it's `0`, while `0` is inactive, `1` is active
- `organization_id [uuid]`: the fkey, reference `organization.id`
- `role_id [uuid]`: the fkey, reference `role.id`
- `auth_id [uuid]`: the fkey, reference `users.id`
- `profile_url [character varying]`: to store url, default is a placeholder image


## record_type
- `id [uuid]`: use as `primary key`
- `created_at [timestamp with time zone]`: by default is `now()`
- `updated_at [timestamp with time zone]`: by default is `now()`
- `created_by [uuid]`: the fkey, reference `officer.id`
- `updated_by [uuid]`: the fkey, reference `officer.id`
- `code [character varying]`: it's `UNIQUE`
- `description [text]`: info
- `is_active [smallint]`: by default it's `0`, while `0` is inactive, `1` is active
- `deletable [smallint]`: by default it's `1`, while `1` is deletable, `0` is not


## record_attribute
- `id [uuid]`: use as `primary key`
- `created_at [timestamp with time zone]`: by default is `now()`
- `updated_at [timestamp with time zone]`: by default is `now()`
- `created_by [uuid]`: the fkey, reference `officer.id`
- `updated_by [uuid]`: the fkey, reference `officer.id`
- `code [character varying]`: it's `UNIQUE`
- `data_type [character varying]`: the data type of the attribute


## record_template
- `id [uuid]`: use as `primary key`
- `created_at [timestamp with time zone]`: by default is `now()`
- `updated_at [timestamp with time zone]`: by default is `now()`
- `created_by [uuid]`: the fkey, reference `officer.id`
- `updated_by [uuid]`: the fkey, reference `officer.id`
- `record_type_id [uuid]`: the fkey, reference `record_type.id`
- `record_attribute_id [uuid]`: the fkey, reference `record_attribute.id`
- `ordering [bigint]`: ordering
- `is_require [smallint]`: `1` for required, `0` for optional


## record
- `id [uuid]`: use as `primary key`
- `created_at [timestamp with time zone]`: by default is `now()`
- `updated_at [timestamp with time zone]`: by default is `now()`
- `created_by [uuid]`: the fkey, reference `officer.id`
- `updated_by [uuid]`: the fkey, reference `officer.id`
- `record_type_id [uuid]`: the fkey, reference `record_type.id`
- `title [character varying]`: the record title
- `status [smallint]`: the record status
- `record_stage_id [uuid]`: the fkey, reference `record_stage_template.id`
- `record_type_code [character varying]`: store the record type code, from `record.code`
- `record_content [text]`: the main content
- `record_metadata [text]`: metadata as text
- `record_time [timestamp with time zone]`: the record timestamp
- `record_tag [text]`: tags as text
- `parent_record [uuid]`: the fkey, reference `record.id`, for self-join
- `record_additional_info [text]`: additional info
- `record_flow_code [character varying]`: by default it's `normal`


## record_attachment
- `id [uuid]`: use as `primary key`
- `created_at [timestamp with time zone]`: by default is `now()`
- `updated_at [timestamp with time zone]`: by default is `now()`
- `created_by [uuid]`: the fkey, reference `officer.id`
- `updated_by [uuid]`: the fkey, reference `officer.id`
- `record_id [uuid]`: the fkey, reference `record.id`
- `reference_id [uuid]`: the fkey, reference `record.id`, for referencing another record


## record_detail
- `id [uuid]`: use as `primary key`
- `created_at [timestamp with time zone]`: by default is `now()`
- `updated_at [timestamp with time zone]`: by default is `now()`
- `created_by [uuid]`: the fkey, reference `officer.id`
- `updated_by [uuid]`: the fkey, reference `officer.id`
- `record_id [uuid]`: the fkey, reference `record.id`
- `record_attribute_code [character varying]`: the fkey, reference `record_attribute.code`
- `value_number [numeric]`: for numeric values
- `value_string [text]`: for string values
- `value_time [timestamp with time zone]`: for datetime values
- `value_boolean [boolean]`: for boolean values
- `value_json [jsonb]`: for json values
- `value_id [uuid]`: for reference id values


## file
- `id [uuid]`: use as `primary key`
- `created_at [timestamp with time zone]`: by default is `now()`
- `updated_at [timestamp with time zone]`: by default is `now()`
- `created_by [uuid]`: the fkey, reference `officer.id`
- `updated_by [uuid]`: the fkey, reference `officer.id`
- `nam [character varying]`: the file name
- `path [character varying]`: the file path
- `file_size [bigint]`: the file size
- `mime_type [character varying]`: the mime type
- `storage_type [character varying]`: the storage type
- `direct_url [text]`: the direct url
- `source_table [character varying]`: the source table reference
- `status [character varying]`: by default it's `active`, enum `[active, trash]`


## record_organization
- `id [uuid]`: use as `primary key`
- `created_at [timestamp with time zone]`: by default is `now()`
- `updated_at [timestamp with time zone]`: by default is `now()`
- `created_by [uuid]`: the fkey, reference `officer.id`
- `updated_by [uuid]`: the fkey, reference `officer.id`
- `record_id [uuid]`: the fkey, reference `record.id`
- `organization_id [uuid]`: the fkey, reference `organization.id`
- `role_type [character varying]`: the role type of the organization in the record, enum `[owner, contributor, reviewer, participant, observer, cc]`


## record_stage_template
- `id [uuid]`: use as `primary key`
- `created_at [timestamp with time zone]`: by default is `now()`
- `updated_at [timestamp with time zone]`: by default is `now()`
- `created_by [uuid]`: the fkey, reference `officer.id`
- `updated_by [uuid]`: the fkey, reference `officer.id`
- `record_type_id [uuid]`: the fkey, reference `record_type.id`
- `ordering [bigint]`: ordering
- `nam [character varying]`: the stage name
- `is_final [smallint]`: by default it's `0`, while `0` is not final, `1` is final stage


## audit_log
- `id [bigint]`: use as `primary key`, `GENERATED ALWAYS AS IDENTITY`
- `created_at [timestamp with time zone]`: by default is `now()`
- `created_by [uuid]`: the fkey, reference `officer.id`
- `action_code [character varying]`: the action code
- `table_name [character varying]`: the target table name
- `row_id [uuid]`: the target row id
- `detail_data [jsonb]`: detail data as json
- `ip_address [text]`: the ip address
- `status_code [character varying]`: by default it's `success`
- `source_log [character varying]`: by default it's `unknown`
- `raw_text [text]`: raw text
- `message [text]`: message


## setting
- `id [uuid]`: use as `primary key`
- `created_at [timestamp with time zone]`: by default is `now()`
- `updated_at [timestamp with time zone]`: by default is `now()`
- `created_by [uuid]`: the fkey, reference `officer.id`
- `updated_by [uuid]`: the fkey, reference `officer.id`
- `key_group [character varying]`: the setting group
- `key [character varying]`: the setting key
- `description [character varying]`: the setting description
- `data_type [character varying]`: the data type
- `public_access [smallint]`: by default it's `0`, while `0` is private, `1` is public
- `visible [smallint]`: by default it's `0`, while `0` is hidden, `1` is visible
- `ordering [integer]`: by default is `0`
- `key_value [character varying]`: the setting value


## notification_audit_log
- `id [bigint]`: use as `primary key`, `GENERATED ALWAYS AS IDENTITY`
- `created_at [timestamp with time zone]`: by default is `now()`
- `log_id [bigint]`: reference to audit_log
- `payload [jsonb]`: notification payload
- `proccessed [boolean]`: by default is `false`


## users (need to change)
- `id [uuid]`: use as `primary key`
- `created_at [timestamp with time zone]`: by default is `now()`
- `updated_at [timestamp with time zone]`: by default is `now()`
- `aud [character varying]`: by default it's `authenticated`
- `role [character varying]`: the user role
- `email [character varying]`: the user email
- `email_confirmed_at [timestamp with time zone]`: email confirmation timestamp
- `phone [character varying]`: the user phone
- `confirmed_at [timestamp with time zone]`: confirmation timestamp
- `last_sign_in_at [timestamp with time zone]`: last sign in timestamp
- `app_metadata [jsonb]`: app metadata
- `user_metadata [jsonb]`: user metadata
- `identities [jsonb]`: identity data
- `created_by [uuid]`: the fkey, reference `officer.id`
- `updated_by [uuid]`: the fkey, reference `officer.id`
- `phone_confirmed_at [timestamp with time zone]`: phone confirmation timestamp


## enum
- `id [bigint]`: use as `primary key`, auto-number
- `created_at [timestamp with time zone]`: by default is `now()`
- `updated_at [timestamp with time zone]`: by default is `now()`
- `created_by [uuid]`: the fkey, reference `officer.id`
- `updated_by [uuid]`: the fkey, reference `officer.id`
- `code [text]`: it's `UNIQUE`
- `value [text]`: the enum value
- `description [text]`: info


## document_type
- `id [uuid]`: use as `primary key`
- `created_at [timestamp with time zone]`: by default is `now()`
- `updated_at [timestamp with time zone]`: by default is `now()`
- `created_by [uuid]`: the fkey, reference `officer.id`
- `updated_by [uuid]`: the fkey, reference `officer.id`
- `nam [character varying]`: it's `UNIQUE`
- `description [text]`: info
- `is_active [smallint]`: by default it's `0`, while `0` is inactive, `1` is active
- `color_code [character varying]`: the color code for display


## officer_identifier
- `id [uuid]`: use as `primary key`
- `created_at [timestamp with time zone]`: by default is `now()`
- `updated_at [timestamp with time zone]`: by default is `now()`
- `created_by [uuid]`: the fkey, reference `officer.id`
- `updated_by [uuid]`: the fkey, reference `officer.id`
- `officer_id [uuid]`: the fkey, reference `officer.id`
- `identifier_type [text]`: the type of identifier
- `identifier [text]`: the identifier value
- `key1 [text]`: additional key