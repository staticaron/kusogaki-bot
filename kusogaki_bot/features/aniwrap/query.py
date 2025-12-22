user_query = """
query($username: String){
  User(name: $username){
    name
    id
  }
}
"""
