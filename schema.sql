-- Supabase → SQL Editor дотор энэ кодыг ажиллуул
-- news.mn мэдээ хадгалах хүснэгт

create table if not exists news (
    link        text primary key,          -- мэдээний URL = давхцал шалгах түлхүүр
    title       text,
    image       text,
    excerpt     text,
    category    text default 'entertainment',
    date_text   text,                       -- "2 цагийн өмнө" / "2026-06-08"
    first_seen  timestamptz default now()   -- АНХ орж ирсэн цаг (шинэчлэхэд хөдөлдөггүй)
);

-- Шинэ мэдээг дээр харуулахын тулд:
create index if not exists idx_news_first_seen on news (first_seen desc);
