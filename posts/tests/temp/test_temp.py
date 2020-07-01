import os
from time import sleep

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test.client import Client
from django.test import TestCase
from django.urls import reverse

from posts.models import Post, Group
from yatube.settings import BASE_DIR, TEMPLATE_CACHE_TIMEOUTS


class TestPosts(TestCase):

    def setUp(self):
        self._unlogged_client = Client()
        self._logged_client = Client()
        user_login_data = dict(username='my_user',
                               password='user_password')
        self._user = User.objects._create_user(**user_login_data,
                                               email='myemail@test.com')
        self._logged_client.force_login(self._user)
        group = Group(title='test group', slug='test_group')
        group.save()
        self._post = Post(text='test post text', group=group)

    def post_publish_data(self, with_image=False):
        res = {'text': self._post.text, 'group': self._post.group.pk}
        if with_image:
            res['image'] = os.path.join(BASE_DIR, 'posts/static/mug.jpg')
        return res

    def check_post_in_posts(self, post_id=None):
        lookup_data = dict(author__username=self._user.username)
        if post_id is not None:
            lookup_data['pk'] = post_id
        res = Post.objects.get(**lookup_data)
        for key, val in self.post_publish_data().items():
            post_val = getattr(res, key)
            if isinstance(post_val, Group):
                self.assertEqual(val, post_val.pk)
            else:
                self.assertEqual(val, post_val)
        return res

    def publish_post_new(self):
        url = reverse('post_new')
        response = self._logged_client.post(url, data=self.post_publish_data(),
                                            follow=True)
        self._post = self.check_post_in_posts()
        self.post_text_is_found_on_post_pages()
        return response

    def get_page_urls_for_post(self, post_id: int = None):
        if post_id is None:
            post_id = self._post.pk
        return {
           'index': {},
           'profile': {'username': self._user.username},
           'group': {'slug': self._post.group.slug},
           'post': {'username': self._user.username, 'post_id': post_id},
        }

    def post_text_is_found_on_post_pages(self, find_img_tag=False):
        urls = self.get_page_urls_for_post()
        for url_name in urls.keys():
            url_kwargs = urls[url_name]
            self.check_page_contains(url_name, self._post.text, url_kwargs)
            if find_img_tag:
                self.check_page_contains(url_name, 'img class="card-img"',
                                         url_kwargs)

    def text_is_not_found_on_post_pages(self, post_text, post_id):
        urls = self.get_page_urls_for_post()
        for url_name in urls.keys():
            url_kwargs = urls[url_name]
            self.check_page_not_contains(url_name, post_text, url_kwargs)

    def get_response_for_unlogged_client(self, url_name: str,
                                         url_kwargs: dict = None):
        url_with_post = reverse(url_name, kwargs=url_kwargs)
        return self._unlogged_client.get(url_with_post, follow=False)

    def check_page_contains(self, url_name: str, contains: str,
                            url_kwargs: dict = None):
        response = self.get_response_for_unlogged_client(url_name, url_kwargs)
        self.assertContains(response, contains)

    def check_page_not_contains(self, url_name: str, not_contains: str,
                                url_kwargs: dict = None):
        response = self.get_response_for_unlogged_client(url_name, url_kwargs)
        self.assertNotContains(response, not_contains)

    def check_edit_post(self):
        url = reverse('post_edit', args=[self._user.username, self._post.pk])
        post_pk = self._post.pk
        self._post.text = 'edited post text'
        response = self._logged_client.post(
            url, data=self.post_publish_data(), follow=True)
        self._post = self.check_post_in_posts(post_id=post_pk)
        return response

    def check_logged_user_can_edit(self, index_cache_timeout=0):
        restore_cache_timeout_to = TEMPLATE_CACHE_TIMEOUTS['index']
        if not index_cache_timeout is None:
            TEMPLATE_CACHE_TIMEOUTS['index'] = index_cache_timeout
        else:
            index_cache_timeout = TEMPLATE_CACHE_TIMEOUTS['index']

        self.publish_post_new()
        self.post_text_is_found_on_post_pages()
        initial_post_text = self._post.text
        post_id = self._post.pk
        self.check_edit_post()

        if index_cache_timeout:
            self.assertGreaterEqual(
                index_cache_timeout, 1,
                ('Increase index_cache_timeout to a value '
                 'greater than 1 for this test to work'))
            sleep(index_cache_timeout - 1)
            self.check_page_contains('index', initial_post_text)
            self.check_page_not_contains('index', self._post.text)
            sleep(1)

        self.text_is_not_found_on_post_pages(initial_post_text, post_id)
        self.post_text_is_found_on_post_pages()

        TEMPLATE_CACHE_TIMEOUTS['index'] = restore_cache_timeout_to


    def test_logged_user_can_edit(self):
        self.check_logged_user_can_edit(index_cache_timeout=0)
        cache.clear()

    # sprint 6

    def test_index_template_cache(self):
        self.check_logged_user_can_edit(index_cache_timeout=3)
        cache.clear()
