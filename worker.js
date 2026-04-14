/**
 * Cloudflare Worker for AI Study Assistant 
 * Proxies requests to Google Gemini API securely.
 */

export default {
  async fetch(request, env, ctx) {
    const corsHeaders = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization",
      "Access-Control-Max-Age": "86400",
    };

    // 1. Handle CORS Preflight requests
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders });
    }

    // 2. Only allow POST requests
    if (request.method !== "POST") {
      return new Response(JSON.stringify({ error: "Method not allowed" }), { 
          status: 405, 
          headers: { ...corsHeaders, "Content-Type": "application/json" } 
      });
    }

    try {
      const url = new URL(request.url);
      // Make routing more flexible by checking if path ends with the expected string
      const path = url.pathname;
      const body = await request.json();

      // Ensure API Key is configured in Cloudflare Dashboard
      const apiKey = env.GEMINI_API_KEY;
      if (!apiKey) {
        return new Response(JSON.stringify({ error: "서버에 API Key가 등록되지 않았습니다." }), { 
            status: 500, 
            headers: { ...corsHeaders, "Content-Type": "application/json" } 
        });
      }

      const geminiEndpoint = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${apiKey}`;

      const responseHeaders = { ...corsHeaders, "Content-Type": "application/json" };

      // Routing
      if (path.endsWith("/api/summarize")) {
        return await handleSummarize(body, geminiEndpoint, responseHeaders);
      } else if (path.endsWith("/api/quiz")) {
        return await handleQuiz(body, geminiEndpoint, responseHeaders);
      } else {
        return new Response(JSON.stringify({ error: `Not Found: ${path}` }), { status: 404, headers: responseHeaders });
      }

    } catch (error) {
      return new Response(JSON.stringify({ error: error.message }), { 
          status: 500, 
          headers: { ...corsHeaders, "Content-Type": "application/json" } 
      });
    }
  },
};

async function handleSummarize(body, endpoint, headers) {
  if (!body.text) {
      return new Response(JSON.stringify({ error: "Text is required" }), { status: 400, headers });
  }

  const systemPrompt = "You are a helpful study assistant. Summarize the following text into 5-10 key bullet points. Please respond in Korean.";
  
  const payload = {
    contents: [{
        parts: [{ text: `${systemPrompt}\n\nText to summarize:\n${body.text}` }]
    }],
    generationConfig: { temperature: 0.5 }
  };

  const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
  });

  if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Gemini API Error: ${errorText}`);
  }

  const data = await response.json();
  const summary = data.candidates[0].content.parts[0].text;

  return new Response(JSON.stringify({ summary }), { headers });
}

async function handleQuiz(body, endpoint, headers) {
  if (!body.summary || !body.quiz_type) {
      return new Response(JSON.stringify({ error: "Summary and quiz_type are required" }), { status: 400, headers });
  }

  const systemPrompt = "You are a helpful study assistant that generates quizzes.";
  const prompt = `다음 요약을 바탕으로 정확히 5개의 퀴즈를 생성해줘. 유형: ${body.quiz_type}.\n\n[요약 내용]\n${body.summary}\n\n질문들은 학생이 이 내용을 공부하는 데 유용해야 해. 정답과 해설은 맨 마지막에 제공해줘. 답변은 한국어로 해줘.`;

  const payload = {
    contents: [{
        parts: [{ text: `${systemPrompt}\n\n${prompt}` }]
    }],
    generationConfig: { temperature: 0.7 }
  };

  const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
  });

  if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Gemini API Error: ${errorText}`);
  }

  const data = await response.json();
  const quiz = data.candidates[0].content.parts[0].text;

  return new Response(JSON.stringify({ quiz }), { headers });
}
