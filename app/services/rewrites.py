from __future__ import annotations

from pathlib import Path

from app.errors import NotFound

# The pseudo-static library aaPanel ships, as nginx rewrite blocks.
LIBRARY: dict[str, dict] = {
    "none": {
        "label": "None",
        "note": "No rewrite rules.",
        "body": "",
    },
    "wordpress": {
        "label": "WordPress",
        "note": "Pretty permalinks.",
        "body": """location / {
    try_files $uri $uri/ /index.php?$args;
}

rewrite /wp-admin$ $scheme://$host$uri/ permanent;
""",
    },
    "laravel": {
        "label": "Laravel",
        "note": "Front controller in public/. Set the run path to /public.",
        "body": """location / {
    try_files $uri $uri/ /index.php?$query_string;
}
""",
    },
    "thinkphp": {
        "label": "ThinkPHP",
        "note": "PATH_INFO routing.",
        "body": """location / {
    if (!-e $request_filename) {
        rewrite ^(.*)$ /index.php?s=$1 last;
        break;
    }
}
""",
    },
    "codeigniter": {
        "label": "CodeIgniter",
        "note": "Removes index.php from URLs.",
        "body": """location / {
    if (!-e $request_filename) {
        rewrite ^/(.*)$ /index.php/$1 last;
        break;
    }
}
""",
    },
    "yii": {
        "label": "Yii 2",
        "note": "Front controller in web/.",
        "body": """location / {
    try_files $uri $uri/ /index.php?$args;
}

location ~ ^/assets/.*\\.php$ {
    deny all;
}
""",
    },
    "symfony": {
        "label": "Symfony",
        "note": "Front controller in public/.",
        "body": """location / {
    try_files $uri /index.php$is_args$args;
}
""",
    },
    "drupal": {
        "label": "Drupal",
        "note": "Clean URLs.",
        "body": """location / {
    try_files $uri /index.php?$query_string;
}

location @rewrite {
    rewrite ^/(.*)$ /index.php?q=$1;
}

location ~ /\\.ht {
    deny all;
}
""",
    },
    "joomla": {
        "label": "Joomla",
        "note": "SEF URLs.",
        "body": """location / {
    try_files $uri $uri/ /index.php?$args;
}

location ~* /(administrator|cache|cli|components|includes|language|libraries|logs|modules|plugins|tmp)/.*\\.(txt|xml|ini)$ {
    deny all;
}
""",
    },
    "typecho": {
        "label": "Typecho",
        "note": "Permalinks.",
        "body": """location / {
    if (!-e $request_filename) {
        rewrite ^(.*)$ /index.php$1 last;
    }
}
""",
    },
    "discuz": {
        "label": "Discuz! X3",
        "note": "Forum rewrite set.",
        "body": """rewrite ^([^\\.]*)/topic-(.+)\\.html$ $1/portal.php?mod=topic&topic=$2 last;
rewrite ^([^\\.]*)/article-([0-9]+)-([0-9]+)\\.html$ $1/portal.php?mod=view&aid=$2&page=$3 last;
rewrite ^([^\\.]*)/forum-(\\w+)-([0-9]+)\\.html$ $1/forum.php?mod=forumdisplay&fid=$2&page=$3 last;
rewrite ^([^\\.]*)/thread-([0-9]+)-([0-9]+)-([0-9]+)\\.html$ $1/forum.php?mod=viewthread&tid=$2&extra=page%3D$4&page=$3 last;
rewrite ^([^\\.]*)/group-([0-9]+)-([0-9]+)\\.html$ $1/forum.php?mod=group&fid=$2&page=$3 last;
rewrite ^([^\\.]*)/space-(username|uid)-(.+)\\.html$ $1/home.php?mod=space&$2=$3 last;
rewrite ^([^\\.]*)/([a-z]+[a-z0-9_]*)-([a-z0-9_\\-]+)\\.html$ $1/plugin.php?id=$2:$3 last;
if (!-e $request_filename) {
    return 404;
}
""",
    },
    "dedecms": {
        "label": "DedeCMS",
        "note": "Article and list rewrites.",
        "body": """rewrite ^/index.html$ /index.php last;
rewrite ^/list-([0-9]+)\\.html$ /plus/list.php?tid=$1 last;
rewrite ^/list-([0-9]+)-([0-9]+)-([0-9]+)\\.html$ /plus/list.php?tid=$1&totalresult=$2&PageNo=$3 last;
rewrite ^/view-([0-9]+)-1\\.html$ /plus/view.php?arcID=$1 last;
rewrite ^/view-([0-9]+)-([0-9]+)\\.html$ /plus/view.php?aid=$1&pageno=$2 last;
rewrite ^/tags\\.html$ /tags.php last;
rewrite ^/tag-([0-9]+)-([0-9]+)\\.html$ /tags.php?/$1/$2/ last;
""",
    },
    "ecshop": {
        "label": "ECShop",
        "note": "Category and goods rewrites.",
        "body": """if (!-e $request_filename) {
    rewrite "^/index\\.html$" /index.php last;
    rewrite "^/category$" /index.php last;
    rewrite "^/feed-c([0-9]+)\\.xml$" /feed.php?cat=$1 last;
    rewrite "^/category-([0-9]+)-b([0-9]+)-min([0-9]+)-max([0-9]+)-attr([^-]*)-([0-9]+)-([^-]+)-([^-]+)\\.html$" /category.php?id=$1&brand=$2&price_min=$3&price_max=$4&filter_attr=$5&page=$6&sort=$7&order=$8 last;
    rewrite "^/goods-([0-9]+)(.*)\\.html" /goods.php?id=$1 last;
    rewrite "^/article-([0-9]+)(.*)\\.html" /article.php?id=$1 last;
    rewrite "^/brand-([0-9]+)-c([0-9]+)(.*)\\.html" /brand.php?id=$1&cat=$2 last;
}
""",
    },
    "phpwind": {
        "label": "phpwind",
        "note": "Forum rewrites.",
        "body": """rewrite ^(.*)-htm-(.*)$ $1.php?$2 last;
rewrite ^(.*)/simple/([a-z0-9_]+\\.html)$ $1/simple/index.php?$2 last;
""",
    },
    "zblog": {
        "label": "Z-BlogPHP",
        "note": "Permalinks.",
        "body": """location / {
    if (!-e $request_filename) {
        rewrite ^/(.*)$ /index.php/$1 last;
    }
}
""",
    },
    "emlog": {
        "label": "Emlog",
        "note": "Permalinks.",
        "body": """rewrite ^/sitemap\\.xml$ /sitemap.php last;
rewrite ^/feed$ /rss.php last;
rewrite ^/post/([0-9]+)$ /?post=$1 last;
rewrite ^/sort/([^/]+)$ /?sort=$1 last;
rewrite ^/tag/([^/]+)$ /?tag=$1 last;
if (!-e $request_filename) {
    rewrite ^/(.*)$ /index.php/$1 last;
}
""",
    },
    "maccms": {
        "label": "MacCMS",
        "note": "Video CMS rewrites.",
        "body": """location / {
    if (!-e $request_filename) {
        rewrite ^(.*)$ /index.php?s=$1 last;
    }
}
""",
    },
    "spa": {
        "label": "Single-page app",
        "note": "History-mode routing for Vue, React or Angular builds.",
        "body": """location / {
    try_files $uri $uri/ /index.html;
}
""",
    },
    "nextjs": {
        "label": "Next.js static export",
        "note": "Trailing-slash friendly static export.",
        "body": """location / {
    try_files $uri $uri.html $uri/index.html /index.html;
}
""",
    },
    "deny-upload-php": {
        "label": "Block PHP in upload folders",
        "note": "Hardening rule. Combine with another template.",
        "body": """location ~* ^/(uploads|upload|images|static|assets|data)/.*\\.(php|php5|phtml|pl|py|jsp|asp|sh|cgi)$ {
    deny all;
}
""",
    },
}


def list_templates() -> list[dict]:
    return [
        {"key": key, "label": item["label"], "note": item["note"], "lines": item["body"].count("\n")}
        for key, item in LIBRARY.items()
    ]


def get_template(key: str) -> dict:
    item = LIBRARY.get(key)
    if not item:
        raise NotFound(f"No pseudo-static template named '{key}'")
    return {"key": key, "label": item["label"], "note": item["note"], "body": item["body"]}


def detect(root: str) -> str:
    """Guess the framework from what is on disk, the way aaPanel pre-selects one."""
    path = Path(root)
    if not path.is_dir():
        return "none"
    markers = [
        ("wordpress", ["wp-config.php", "wp-login.php", "wp-content"]),
        ("laravel", ["artisan", "bootstrap/app.php"]),
        ("symfony", ["bin/console", "symfony.lock"]),
        ("yii", ["yii", "requirements.php"]),
        ("thinkphp", ["think", "thinkphp"]),
        ("codeigniter", ["system/CodeIgniter.php", "spark"]),
        ("drupal", ["core/lib/Drupal.php", "sites/default/settings.php"]),
        ("joomla", ["configuration.php", "administrator/manifests"]),
        ("typecho", ["config.inc.php", "var/Typecho"]),
        ("discuz", ["forum.php", "source/class/class_core.php"]),
        ("dedecms", ["dede", "plus/list.php"]),
        ("ecshop", ["goods.php", "includes/init.php"]),
        ("zblog", ["zb_system", "zb_users"]),
        ("emlog", ["admin/index.php", "include/lib/option.php"]),
        ("nextjs", ["_next", "next.config.js"]),
    ]
    for key, needles in markers:
        if any((path / needle).exists() for needle in needles):
            return key
    if (path / "index.html").is_file() and not any(path.glob("*.php")):
        return "spa"
    return "none"
