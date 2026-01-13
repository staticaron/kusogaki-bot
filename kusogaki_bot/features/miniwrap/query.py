user_query = """
query($username: String){
  User(name: $username){
    name
    id
  }
}
"""

media_image_query = """
query ($mediaID: Int) {
  Media(id: $mediaID) {
    coverImage {
      large
    }
  }
}
"""
