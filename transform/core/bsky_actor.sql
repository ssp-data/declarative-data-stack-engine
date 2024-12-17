WITH user_posts AS (
    SELECT 
        actor_did,
        COUNT(*) as total_posts,
        COUNT(CASE WHEN is_reply THEN 1 END) as total_replies,
        COUNT(CASE WHEN NOT is_reply THEN 1 END) as original_posts,
        COUNT(DISTINCT language) as languages_used
    FROM ddse.pub.bsky_posts
    GROUP BY actor_did
),
user_likes AS (
    SELECT 
        actor_did,
        COUNT(*) as likes_given
    FROM ddse.pub.bsky_likes
    GROUP BY actor_did
),
user_follows AS (
    SELECT 
        actor_did,
        COUNT(*) as follows_count
    FROM ddse.pub.bsky_follow
    GROUP BY actor_did
),
user_reposts AS (
    SELECT 
        actor_did,
        COUNT(*) as reposts_count
    FROM ddse.pub.bsky_reposts
    GROUP BY actor_did
),
likes_received AS (
    SELECT 
        p.actor_did,
        COUNT(l.uri) as total_likes_received
    FROM ddse.pub.bsky_posts p
    LEFT JOIN ddse.pub.bsky_likes l ON p.uri = l.uri
    GROUP BY p.actor_did
),
reposts_received AS (
    SELECT 
        p.actor_did,
        COUNT(r.uri) as total_reposts_received
    FROM ddse.pub.bsky_posts p
    LEFT JOIN ddse.pub.bsky_reposts r ON p.uri = r.uri
    GROUP BY p.actor_did
)

SELECT 
    p.actor_did,
    p.total_posts,
    p.total_replies,
    p.original_posts,
    p.languages_used,
    COALESCE(l.likes_given, 0) as likes_given,
    COALESCE(f.follows_count, 0) as follows_count,
    COALESCE(r.reposts_count, 0) as reposts_count,
    COALESCE(lr.total_likes_received, 0) as likes_received,
    COALESCE(rr.total_reposts_received, 0) as reposts_received,
    -- Basic engagement ratios
--    ROUND(COALESCE(lr.total_likes_received, 0)::float / NULLIF(p.total_posts, 0), 2) as avg_likes_per_post,
--    ROUND(COALESCE(rr.total_reposts_received, 0)::float / NULLIF(p.total_posts, 0), 2) as avg_reposts_per_post
FROM user_posts p
LEFT JOIN user_likes l ON p.actor_did = l.actor_did
LEFT JOIN user_follows f ON p.actor_did = f.actor_did
LEFT JOIN user_reposts r ON p.actor_did = r.actor_did
LEFT JOIN likes_received lr ON p.actor_did = lr.actor_did
LEFT JOIN reposts_received rr ON p.actor_did = rr.actor_did
WHERE p.total_posts > 0
ORDER BY p.total_posts DESC;
