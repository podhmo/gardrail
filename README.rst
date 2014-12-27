gardrail
========================================

gardrail is strange dict validation library.

quick example
----------------------------------------

this is a user registration situation.

.. code:: python

    from gardrail import (
        Gardrail,
        NG, Failure,
        multi,
        single
    )


    class DB(object):
        def __init__(self, data):
            self.data = data

        def save(self, user):
            self.data.append(user)

        def __iter__(self):
            return iter(self.data)


    class UserRegistrationValidation(Gardrail):
        def __init__(self, db):
            self.db = db

        @single("email", strict=True)
        def email_check(self, email):
            if any(ob["email"] == email for ob in self.db):
                return NG("already registered")

        @multi(["password", "re-password"], strict=True)
        def password_check(self, password, re_password):
            if password != re_password:
                return NG("not same")

    # first registration is success
    db = DB([])
    validation = UserRegistrationValidation(db)
    result = validation({"email": "foo@gmail.com",
                         "password": "foo",
                         "re-password": "foo"})
    print(result)
    # => {'re-password': 'foo', 'email': 'foo@gmail.com', 'password': 'foo'}
    db.save(result)


    # if password and re-password is not same, validation error
    try:
        result = validation({"email": "boo@gmail.com",
                             "password": "boo",
                             "re-password": "bxx"})
    except Failure as e:
        print(e)
        # => {'password': ['not same']}


    # if already registered by same email address, validation error
    try:
        result = validation({"email": "foo@gmail.com",
                             "password": "foo",
                             "re-password": "foo"})
    except Failure as e:
        print(e)
        # => {'email': ['already registered']}

strict option is True, then, each fields treated as mandatory.

.. code:: python

    try:
        result = validation({})
    except Failure as e:
        print(e)
        # => {'password': ["fields:['password', 're-password'] not found: Multi.<function UserRegistrationValidation.password_check at 0x109ad1560>"], 'email': ["fields:['email'] not found: Multi.<function UserRegistrationValidation.email_check at 0x109ad1290>"]}


    # custom Validation

    # changing message about strict true option validation is failured.
    class OurUserRegistrationValidation(UserRegistrationValidation):
        def on_missing(self, names, validator_name, fn):
            return NG("notfound: {}".format(names))

    try:
        my_validation = OurUserRegistrationValidation({})
        result = my_validation({})
    except Failure as e:
        print(e)
        # => {'password': ["notfound: ['password', 're-password']"], 'email': ["notfound: ['email']"]}


validation decorator
----------------------------------------

Each validation of gardrail is defined by a special decorator.
Defined decorators are below.

- multi
- single
- (share)
- matched
- convert
- subrail
- container
- collection

TODO: write detail.

multi
----------------------------------------
