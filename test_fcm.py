from rustplus import FCMListener
import json

fcm_creds = {
    "expo_push_token": "ExponentPushToken[1QbJpeGqrLMlMZO3K6J2I0]",
    "fcm_credentials": {
        "fcm": {
            "token": "d8Ndz3kDsJ8:APA91bEKdi2ewvGwmiHd_an0XndDHA22gIdDUgHsuLlgETEr4WAWbXC64oXfYza-4MU9KCwGRzuCsoHhfMkkHfvFXOwfr16gA2rTknhlbWjTkkZ4b2AUFMU"
        },
        "gcm": {
            "androidId": "4960995966111507824",
            "securityToken": "7226754990601961515"
        }
    }
}

class TestFCM(FCMListener):
    def on_notification(self, obj, notification, data_message):
        print("\n" + "="*50)
        print("📬 NOTIFICATION RECEIVED!")
        print("="*50)
        if notification:
            print("Notification:", json.dumps(notification, indent=2))
        if data_message:
            print("Data:", json.dumps(data_message, indent=2))
        print("="*50 + "\n")

print("🎧 Starting FCM test listener...")
print("📱 Go in-game and pair a device NOW!")
print("⏳ Waiting...\n")

TestFCM(fcm_creds).start()