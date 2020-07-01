from django.forms import ModelForm, Textarea

from posts.models import Post, Comment


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('group', 'text', 'image')
        labels = {
            'group': 'Группа',
            'text': 'Текст',
            'image': 'Изображение',
        }
        help_texts = {
            'group': 'Выберите группу, в которой будет опубликован пост',
            'text': 'Введите текст поста для публикации',
            'image': 'Введите заглавное изображение поста',
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            'text': Textarea(attrs={'cols': 80, 'rows': 20}),
        }
