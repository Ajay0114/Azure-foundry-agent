# PC_HomeDelivery_Script_TransactionsErrorHandling  (script)

## Config
```json
{
  "name": "PC_HomeDelivery_Script_TransactionsErrorHandling",
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

    var transactionResponse =
        context.PC_HomeDelivery_DocumentCreation_Service_Transcations &&
        context.PC_HomeDelivery_DocumentCreation_Service_Transcations.response;

    var transactionStatus =
        transactionResponse &&
        transactionResponse.body &&
        transactionResponse.body.status;

    if (
        transactionStatus &&
        String(transactionStatus) !== "201"
    ) {

        var tb = transactionResponse.body;

        var transactionError =
            tb &&
            tb.errorDetails &&
            tb.errorDetails[0] &&
            tb.errorDetails[0].message
                ? tb.errorDetails[0].message
                : (
                    tb.errorMessage ||
                    tb.title ||
                    "Unknown API Error"
                );

        errorMessages.push(
            "Transaction Document (Status: " +
            transactionStatus +
            "): " +
            transactionError
        );
    }

} catch (e) {

    koreDebugger.log(
        "Error reading Transaction response: " +
        e.message
    );
}

var noteBody =
    "<b>TRANSACTION DOCUMENT CREATION FAILED</b><br>" +
    "---------------------<br><br>" +
    "<b>Error Details:</b><br>" +
    (errorMessages.length
        ? errorMessages.join("<br>")
        : "Unknown Error") +
    "<br><br>" +
    "As a result, the transaction document creation request could not be processed.";

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
    "Transaction Document error note: " +
    context.docErrorNotePayload
);
```
