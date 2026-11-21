def can_moderate(user, article):
    if not user.is_authenticated:
        return False
    return user.is_blog_admin or (user.is_author and article.author_id == user.id)