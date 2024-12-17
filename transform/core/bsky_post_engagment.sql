WITH engagement_data AS (
  SELECT 
    RIGHT(post_data.post.uri, 13) as post_uri,
    --post_data.post.uri as post_uri,
    post_data.post.author.handle,
    LEFT(post_data.post.record.text, 50) as post_text,
    post_data.post.record.createdAt as created_at,
    (post_data.post.replyCount + 
     post_data.post.repostCount + 
     post_data.post.likeCount + 
     post_data.post.quoteCount) as total_engagement,
      post_data.post.replyCount as replies,
      post_data.post.repostCount as reposts,
      post_data.post.likeCount as likes,
      post_data.post.quoteCount as quotes,
  FROM ddse.pub.bsky_posts
)
SELECT 
  post_uri,
  created_at,
  total_engagement,
  bar(total_engagement, 0, 
      (SELECT MAX(total_engagement) FROM engagement_data), 
      30) as engagement_chart,
  replies, reposts, likes, quotes,
  post_text,

FROM engagement_data
--WHERE handle = 'ssp.sh'
ORDER BY total_engagement DESC
LIMIT 30;  
