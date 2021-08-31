from models import Admin,Agent,Client

## helpers to simulate a swith case statement
###########################################################################################

def admin(id):
    admin = Admin.query.get(id)
    return admin.serialize()
        
def agent(id):
    agent = Agent.query.get(id)
    return agent.serialize()

def client(id):
    client = Client.query.get(id)
    return client.serialize()

###########################################################################################