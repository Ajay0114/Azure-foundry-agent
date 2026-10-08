# PC_HomeDelivery_Script_BookingRoute  (script)

## Config
```json
{
  "name": "PC_HomeDelivery_Script_BookingRoute",
  "type": "script"
}
```

## script
```
try {
    var ENT = "PC_HomeDelivery_Entity_BookingNumber";

    koreDebugger.log("BOOKING | ENTITIES: " + JSON.stringify(context.entities));

    var s = context.session.BotUserSession = context.session.BotUserSession || {};
    s.bookingAttempt = s.bookingAttempt || 0;

    // clean up the phantom key written by the earlier version
    if (context.entities && context.entities.BookingNumber !== undefined) {
        delete context.entities.BookingNumber;
    }

    // capture BEFORE any clearing, the entity slot is volatile
    var typedValue = context.entities[ENT] || null;

    var raw = context.GenerativeAINode &&
              context.GenerativeAINode.PC_HomeDelivery_BookingClassifier &&
              context.GenerativeAINode.PC_HomeDelivery_BookingClassifier.text;

    var parsed = null;
    if (raw) {
        var clean = String(raw).replace(/```json|```/g, "").trim();
        try {
            parsed = JSON.parse(clean);
        } catch (eParse) {
            koreDebugger.log("BOOKING | JSON Parse Error: " + eParse.message);
        }
    }

    function commitBooking(val) {
        var bn = String(val).trim();
        context.entities[ENT]   = bn;   // volatile
        context.bookingNumber   = bn;   // dialog scope
        s.BookingNumber         = bn;   // session scope
        s.resolvedBookingNumber = bn;   // matches existing pattern
        s.BookingNumberUnknown  = false;
    }

    function skipBooking() {
        delete context.entities[ENT];
        context.bookingNumber   = null;
        s.BookingNumber         = null;
        s.resolvedBookingNumber = null;
        s.BookingNumberUnknown  = true;
    }

    if (!parsed) {
        // fail open: keep whatever was typed rather than trapping the user
        if (typedValue) { commitBooking(typedValue); }
        else            { skipBooking(); }
        context.bookingRoute = s.bookingRoute = "accept";
        koreDebugger.log("BOOKING | No classifier output, accepted raw value");

    } else {
        var cat = String(parsed.category || "unclear").toLowerCase().trim();
        s.bookingAttempt = s.bookingAttempt + 1;

        if (cat === "valid" &&
            parsed.booking_number !== null &&
            String(parsed.booking_number).trim() !== "") {

            commitBooking(parsed.booking_number);
            context.bookingRoute = s.bookingRoute = "accept";

        } else if (cat === "unknown") {
            // do not re-ask someone who already said they cannot supply it
            skipBooking();
            context.bookingRoute = s.bookingRoute = "fallback";

        } else if (s.bookingAttempt < 3) {
            delete context.entities[ENT];   // required for re-ask
            context.bookingRoute = s.bookingRoute = "retry";

        } else {
            skipBooking();
            context.bookingRoute = s.bookingRoute = "fallback";
        }

        context.bookingCategory  = s.bookingCategory = cat;
        s.bookingIdentifierGiven = parsed.identifier_given || null;
    }

    koreDebugger.log("BOOKING | " + JSON.stringify({
        attempt:  s.bookingAttempt,
        category: s.bookingCategory,
        route:    s.bookingRoute,
        typed:    typedValue,
        stored:   s.BookingNumber
    }));

} catch (e) {
    var sc = context.session.BotUserSession = context.session.BotUserSession || {};
    context.bookingRoute = sc.bookingRoute = "accept";
    koreDebugger.log("BOOKING | Script Error: " + e.message);
}
```
