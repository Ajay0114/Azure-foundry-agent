# PC_HomeDelivery_Script_ReturnsErrorHandling  (script)

## Config
```json
{
  "name": "PC_HomeDelivery_Script_ReturnsErrorHandling",
  "type": "script"
}
```

## script
```
context.session = context.session || {};
context.session.BotUserSession = context.session.BotUserSession || {};

var s = context.session.BotUserSession;

var errorMessages = [];

try {

    var returnResponse =
        context.DocumentCreation_Service_Returns &&
        context.DocumentCreation_Service_Returns.response;

    var returnStatus =
        returnResponse &&
        returnResponse.body &&
        returnResponse.body.status;

    if (returnStatus && String(returnStatus) !== "201") {

        var rb = returnResponse.body;

        var returnError =
            rb &&
            rb.errorDetails &&
            rb.errorDetails[0] &&
            rb.errorDetails[0].message
                ? rb.errorDetails[0].message
                : (
                    rb.errorMessage ||
                    rb.title ||
                    "Unknown API Error"
                );

        errorMessages.push(
            "Returns Document (Status: " +
            returnStatus +
            "): " +
            returnError
        );
    }

} catch (e) {

    koreDebugger.log(
        "Error reading Returns response: " +
        e.message
    );
}

var noteBody =
    "<b>RETURNS DOCUMENT CREATION FAILED</b><br>" +
    "---------------------<br><br>" +
    "<b>Error Details:</b><br>" +
    (errorMessages.length
        ? errorMessages.join("<br>")
        : "Unknown Error") +
    "<br><br>" +
    "As a result, the returns document creation request could not be processed.";

var errorNotePayload = {
    ticket: {
        comment: {
            html_body: noteBody,
            public: false
        }
    }
};

context.docErrorNotePayload =
    JSON.stringify(errorNotePayload);

context.TicketNumber =
    s.TicketId || "";

koreDebugger.log(
    "Returns Document error note: " +
    context.docErrorNotePayload
);
```
