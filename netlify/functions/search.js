// 키워드에서 검색어와 필터 단어 추출
// 예: "라라스윗딸기듬뿍바" → searchQuery: "딸기듬뿍바", filterWord: "딸기듬뿍바"
// 예: "애플망고생요거트바" → searchQuery: "애플망고생요거트바", filterWord: "애플망고생요거트바"
function getSearchQuery(keyword) {
  const brand = "라라스윗";
  if (keyword.startsWith(brand)) {
    const productName = keyword.slice(brand.length); // 라라스윗 제거
    return { searchQuery: productName, filterWord: productName };
  }
  return { searchQuery: keyword, filterWord: keyword };
}

// 결과 필터링: 제목+내용에 filterWord 포함된 것만
function filterResults(items, filterWord) {
  return items.filter(item => {
    const title = (item.title || '').toLowerCase();
    const desc = (item.description || item.content || '').toLowerCase();
    const source = (item.bloggername || item.cafename || item.source || '').toLowerCase();
    const fw = filterWord.toLowerCase();
    return title.includes(fw) || desc.includes(fw) || source.includes(fw);
  });
}

exports.handler = async function(event) {
  const { query, type } = event.queryStringParameters || {};

  if (!query || !type) {
    return { statusCode: 400, body: JSON.stringify({ error: "query and type required" }) };
  }

  const { searchQuery, filterWord } = getSearchQuery(query);

  // 유튜브 검색
  if (type === 'youtube') {
    const YOUTUBE_API_KEY = process.env.YOUTUBE_API_KEY;
    if (!YOUTUBE_API_KEY) {
      return { statusCode: 500, body: JSON.stringify({ error: "YouTube API key not configured" }) };
    }
    const url = `https://www.googleapis.com/youtube/v3/search?part=snippet&q=${encodeURIComponent(searchQuery)}&type=video&order=date&maxResults=50&key=${YOUTUBE_API_KEY}`;
    try {
      const response = await fetch(url);
      const data = await response.json();
      const allItems = (data.items || []).map(item => ({
        title: item.snippet.title,
        link: `https://www.youtube.com/watch?v=${item.id.videoId}`,
        source: item.snippet.channelTitle,
        date: item.snippet.publishedAt.slice(0, 10),
        content: item.snippet.description,
        platform: '유튜브',
      }));
      // 필터링
      const filtered = allItems.filter(item => {
        const title = (item.title || '').toLowerCase();
        const content = (item.content || '').toLowerCase();
        const fw = filterWord.toLowerCase();
        return title.includes(fw) || content.includes(fw);
      });
      return {
        statusCode: 200,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(filtered)
      };
    } catch (e) {
      return { statusCode: 500, body: JSON.stringify({ error: e.message }) };
    }
  }

  // 네이버 검색
  const CLIENT_ID = process.env.NAVER_CLIENT_ID;
  const CLIENT_SECRET = process.env.NAVER_CLIENT_SECRET;

  if (!CLIENT_ID || !CLIENT_SECRET) {
    return { statusCode: 500, body: JSON.stringify({ error: "API keys not configured" }) };
  }

  const url = `https://openapi.naver.com/v1/search/${type}.json?query=${encodeURIComponent(searchQuery)}&display=50&sort=date`;

  try {
    const response = await fetch(url, {
      headers: {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET,
      }
    });
    const data = await response.json();
    const allItems = data.items || [];
    // 필터링
    const filtered = filterResults(allItems, filterWord);
    return {
      statusCode: 200,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(filtered)
    };
  } catch (e) {
    return { statusCode: 500, body: JSON.stringify({ error: e.message }) };
  }
}; 
