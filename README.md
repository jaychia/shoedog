# shoedog
A flexible, efficient plug-and-play query engine built on top of SQLAlchemy, inspired by GraphQL

# Setting up
```
from shoedog import shoedoggify
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)

shoedoggify(app, db)
```

The above code will set up a `/shoedog` endpoint on your application that takes a `POST` request. The payload on the `POST` request is a shoedog payload, with the following syntax:

```
Company {
    name
    year_founded [(* > 1994 and * < 2017) or * == 2019]
    investors {
        name [any in ['gv', a16z']]
        amount_invested [all > 2000000]
    }
    contact_details (SingaporeContact) {
        address
        singapore_contact_number
    }
}
```

The above query will return a json response containing all instances of Company where:
1. The year founded is between 1994 and 2017, or is exactly 2019
2. The investors have all invested over 2,000,000 dollars
3. The investors include at least one investor with a name that is either 'gv' or 'a16z'

Furthermore, the json response has a predictable structure, returning only the fields that were requested.

```
{'companies': [{
    'name': 'XYZ Company',
    'year_founded': 1995,
    'investors': [{
        'name': 'gv',
        'amount_invested': 2000001 
    }],
    'contact_details': {
        'address': '123 Foobar Road',
        'singapore_contact_number': '+65 9635 9999'
    }
}, ...]}
```

Notice that
1. The `contact_details` was returned as a dictionary, since it is a different model.
2. The `contact_details` field was cast as a `SingaporeContact`, which allows us to query for the `singapore_contact_number` field which is only on that particular subclass. This query would have failed without the cast!