Holiday Showdown Alexa Skill
============================

### Flask-ASK

[Flask-ASK](https://github.com/johnwheeler/flask-ask) is an extension of a flask ask that handles and serves the json necessary for
communications between individual alexas and the api. You can wrap methods with `@ask.intent`
while specifying the intent name and necessary slots as seen in `showdown.py`.

### Alexa Flask-ASK Guide library

[AFG](https://github.com/dgtony/afg) let's you provide a schema for conversational logic and essentially serves as a context
manager for your intents. For skills with many intents and/or intents where context within
the conversation matters, this is very useful. You can specify the schema for the conversation
flow within a `.yaml` or `.yml` file and link to it within your Flask-ASK app. Finally, you
need to wrap your intent functions that are context based with `@sup.guide` to ensure that they
are handled by `afg`.

### Zappa

[Zappa](https://github.com/Miserlou/Zappa) serverless python is a very hands-off way of turning your python application into an AWS
API gateway. It automatically detects if you are using a flask app and once it finishes making
the gateway, it returns the https endpoint that your alexa skill can query.
