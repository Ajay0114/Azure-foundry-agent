# PC_HomeDelivery_Script_Booking-and-Credit_Info  (script)

## Config
```json
{
  "name": "PC_HomeDelivery_Script_Booking-and-Credit_Info",
  "type": "script"
}
```

## script
```
if (
    context.entities &&
    context.entities.PC_HomeDelivery_Entity_BookingNumber
) {
    context.session.BotUserSession.bookingNumber =
        context.entities.PC_HomeDelivery_Entity_BookingNumber;
}

if (
    context.entities &&
    context.entities.PC_HomeDelivery_Entity_CreditCardInfo
) {
    context.session.BotUserSession.creditCardLast4Digits =
        context.entities.PC_HomeDelivery_Entity_CreditCardInfo;
}
```
