# PC_CruiseDate_Entities  (script)

## Config
```json
{
  "name": "PC_CruiseDate_Entities",
  "type": "script"
}
```

## script
```
try {

    context.session = context.session || {};
    context.session.BotUserSession = context.session.BotUserSession || {};
    context.entities = context.entities || {};

    var session = context.session.BotUserSession;
    var ent = context.entities;

    function normalizeDate(d) {
        if (!d) return null;

        if (typeof d === "string") {
            return d;
        }

        if (typeof d === "object") {

            if (!d.day || !d.month || !d.year) {
                return null;
            }

            var monthMap = {
                January: "01",
                February: "02",
                March: "03",
                April: "04",
                May: "05",
                June: "06",
                July: "07",
                August: "08",
                September: "09",
                October: "10",
                November: "11",
                December: "12"
            };

            return d.year + "-" +
                   monthMap[d.month] + "-" +
                   String(d.day).padStart(2, "0");
        }

        return null;
    }

    if (ent.start_date) {
        session.usr_start_date = normalizeDate(ent.start_date);
    }

    if (ent.end_date) {
        session.usr_end_date = normalizeDate(ent.end_date);
    }

    // Clear last user message
    if (
        context.session.lastMessage &&
        context.session.lastMessage.messagePayload &&
        context.session.lastMessage.messagePayload.message
    ) {

        context.session.lastMessage.messagePayload.message.body = "";

        koreDebugger.log(
            "DATE SCRIPT | last user message cleared"
        );
    }

    koreDebugger.log(
        "DATE SCRIPT | usr_start_date: " +
        session.usr_start_date
    );

    koreDebugger.log(
        "DATE SCRIPT | usr_end_date: " +
        session.usr_end_date
    );

} catch (e) {

    koreDebugger.log(
        "DATE SCRIPT ERROR: " + e
    );

}
```
