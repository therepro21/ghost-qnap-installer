import fs from 'node:fs';
import GhostAdminAPI from '@tryghost/admin-api';
const file = process.argv[2];
if (!file) throw new Error('Aufruf: ./publish-story stories/beitrag.json');
if (!process.env.GHOST_ADMIN_URL || !process.env.GHOST_ADMIN_KEY) throw new Error('GHOST_ADMIN_URL und GHOST_ADMIN_KEY in .env eintragen.');
const story = JSON.parse(fs.readFileSync(file, 'utf8'));
const api = new GhostAdminAPI({url: process.env.GHOST_ADMIN_URL, key: process.env.GHOST_ADMIN_KEY, version: 'v6.0'});
const uploaded = {};
for (const image of story.images || []) {
  const result = await api.images.upload({file: image.path});
  uploaded[image.path] = result.url;
}
let html = story.html || '';
for (const [local, remote] of Object.entries(uploaded)) html = html.replaceAll(`{{image:${local}}}`, remote);
const post = await api.posts.add({title: story.title, html,
  status: story.status === 'published' ? 'published' : 'draft',
  tags: (story.tags || []).map(name => ({name})),
  feature_image: story.feature_image ? (uploaded[story.feature_image] || story.feature_image) : undefined,
  custom_excerpt: story.excerpt, meta_title: story.meta_title, meta_description: story.meta_description
}, {source: 'html'});
console.log(JSON.stringify({id: post.id, title: post.title, status: post.status, url: post.url}, null, 2));
