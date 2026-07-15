/** @odoo-module **/

import { DateTimeField } from "@web/views/fields/datetime/datetime_field";
import { localization } from "@web/core/l10n/localization";
import { registry } from "@web/core/registry";

/**
 * Keep datetime fields on the friendly medium format in edit mode as well:
 * e.g. "Jul 3, 2:56 PM" (year omitted for the current year).
 *
 * Readonly already uses toLocaleDateTimeString(). Edit mode normally switches
 * to a numeric input using localization.dateTimeFormat (07/03/2026 02:56:49 PM).
 *
 * We replace the DateTimeField template so fields with a value keep the friendly
 * button while focused/editing, and align language formats for empty inputs.
 */

DateTimeField.template = "zilancer_customisation.DateTimeField";

registry.category("services").add("zilancer_friendly_datetime_format", {
    dependencies: ["localization"],
    start() {
        // Empty inputs / typed values use this format instead of MM/dd/yyyy hh:mm:ss a
        localization.dateFormat = "MMM d, yyyy";
        localization.timeFormat = "h:mm a";
        localization.dateTimeFormat = "MMM d, yyyy, h:mm a";
    },
});
