#include <iostream>
#include <fstream>
#include <string>
#include <cstdio>
#include <unistd.h>
#include <curl/curl.h>
#include <vector>
#include <sstream>
#include <deque>

std::string r_file = "r_content.txt";
std::string w_all_file = "all_contents.txt";
std::string w_file = "tmp_content.txt";
std::string history_file = "history.txt";

void deleteFile(const std::string &filename)
{
    if (std::remove(filename.c_str()) != 0)
    {
        std::cerr << "无法删除文件: " << filename << std::endl;
    }
    else 
    {
        std::cout << "文件删除成功: " << filename << std::endl;
    }
}

bool readFile (const std::string &filename, std::string &content, bool flag)
{
    std::ifstream file(filename);
    if (!file.is_open())
        return false;

    std::string line;
    while (std::getline(file, line))
    {
        content += line + "\n"; // 读取每一行并添加换行符
    }

    file.close(); // 关闭文件
    if (flag)
        deleteFile(filename);
    return true;
}

void writeFile(const std::string &filename, const std::string &content, bool append)
{
    std::ofstream file;
    std::ios_base::openmode mode = std::ios::out; // 基本的输出模式
    if (append)
    {
        mode |= std::ios::app; // 如果需要追加,加入 app 模式
    }
    file.open(filename, mode);

    if (!file)
    {
        std::cerr << "无法打开文件: " << filename << std::endl;
        return;
    }

    file << content;
    file.close();
}

size_t WriteCallback(void *contents, size_t size, size_t nmemb, void *userp)
{
    ((std::string *)userp)->append((char *)contents, size * nmemb);
    return size * nmemb;
}

std::string extractContentFromResponse(const std::string &jsonResponse)
{
    std::string contentKey = "\"content\":\"";
    auto contentPos = jsonResponse.find(contentKey);

    if (contentPos == std::string::npos)
    {
        return ""; // 未找到 "content" 字段
    }

    contentPos += contentKey.length(); // 移到实际内容的起始位置
    auto endQuotePos = jsonResponse.find("\"", contentPos);

    if (endQuotePos == std::string::npos)
    {
        return ""; // 未找到内容的结束引号
    }

    return jsonResponse.substr(contentPos, endQuotePos - contentPos);
}

std::string remove_newlines(const std::string &str)
{
    std::string result;
    for (char c : str)
    {
        if (c != '\n' && c != '\r')
        {
            result += c;
        }
    }
    return result;
}

std::vector<std::string> splitString(const std::string &str, char delimiter)
{
    std::vector<std::string> tokens;
    std::istringstream iss(str);
    std::string token;
    while (std::getline(iss, token, delimiter))
    {
        tokens.push_back(token);
    }
    return tokens;
}

std::string createJsonMessages(const std::string &content, const std::string &history)
{
    std::string jsonMessages = R"([)";
    // Add a system message
    // jsonMessages += R"({"role": "system", "content": "{\"prompt_id\":\"a123456\",\"prompt_template_params\":{}}"},)";

    // Split the history string by newline characters
    std::vector<std::string> lines = splitString(history, '\n');

    // Iterate over the lines of history
    for (const auto &line : lines)
    {
        if (line.empty())
            continue; // Skip empty lines

        size_t colon_pos = line.find(':');
        if (colon_pos != std::string::npos)
        {
            std::string role = line.substr(0, colon_pos);
            std::string message = line.substr(colon_pos + 1);

            // Trim whitespace from role and message
            role.erase(role.find_last_not_of(" \t\n\r\f\v") + 1);
            message.erase(0, message.find_first_not_of(" \t\n\r\f\v"));

            role = (role == "User") ? "user" : "assistant";

            jsonMessages += R"({"role": ")" + role + R"(", "content": ")" + message + R"("},)";
        }
    }
    // std::string ss = "你扮演一个温柔有爱善解人意智慧的12岁姐姐,你的对话对象是3岁-6岁的儿童,你的职责是情感陪护,陪儿童聊天,教儿童知识,逗儿童开心,给予儿童情感价值,培养儿童有正确的三观。禁止说出有关黄赌毒和不雅的词语,不能教儿童做坏事。";
    static bool flag = true;
    std::string ss = "";
    if(flag)
    {
        flag = false;
        ss = "我的名字叫小王，我喜欢玩皮球，我今年四岁半。你是一个温柔有爱善解人意智慧的小熊,你的对话对象是3岁-6岁的儿童,你的职责是情感陪护,陪儿童聊天,你是一个儿童对话专家,你会学习模仿孩子说话的方式,教儿童知识,逗儿童开心,给予儿童情感价值,正向鼓励孩子,你想要让孩子开心愉快,培养儿童有正确的三观。禁止说出有关黄赌毒和不雅的词语,不能教儿童做坏事";

    }

    // Add the current user message
    jsonMessages += R"({"role": "user", "content": ")" + ss + remove_newlines(content) + R"("})";

    jsonMessages += R"(])";

    return jsonMessages;
}

void reduceHistory(std::string &history)
{
    int n = 20;
    std::ifstream infile(history);
    std::deque<std::string> lines;
    std::string line;

    if (!infile)
    {
        std::cerr << "无法打开文件: " << history << std::endl;
        return;
    }

    // 读取所有行到双端队列中
    while (std::getline(infile, line))
    {
        lines.push_back(line);
        // 只保留最新的 n 行
        if (lines.size() > n)
        {
            lines.pop_front();
        }
    }
    infile.close();

    // 打开文件以进行写入,覆盖原文件内容
    std::ofstream outfile(history);
    if (!outfile)
    {
        std::cerr << "无法写入文件: " << history << std::endl;
        return;
    }

    // 把最近的 20 行写回文件
    for (const auto &l : lines)
    {
        outfile << l << std::endl;
    }
    outfile.close();
}

void getHistory(std::string &history)
{
    reduceHistory(history_file);
    readFile(history_file, history, false);
}

// ERNIE-Character-8K
// 360gpt-pro
void chatWithGPT(std::string &content, std::string &history, std::string &response)
{
    CURL *curl;
    CURLcode res;
    std::string tmp_res;

    curl = curl_easy_init();
    if (curl)
    {
        std::string jsonMessages = createJsonMessages(content, history);
        // std::string payload = R"({
        //     "model": "360gpt-pro",
        //     "messages": )" + jsonMessages +
        //                       R"(,
        //     "stream": false,
        //     "temperature": 0.9,
        //     "max_tokens": 2048,
        //     "top_p": 0.5,
        //     "top_k": 0,
        //     "repetition_penalty": 1.05,
        //     "num_beams": 1,
        //     "user": "andy"
        // })";
        std::string payload = R"({
            "model": "gpt-4o",
            "prompt": "你是一个温柔有爱善解人意智慧的12岁姐姐,你的对话对象是3岁-6岁的儿童,你的职责是情感陪护,陪儿童聊天,你是一个儿童对话专家,你会学习模仿孩子说话的方式,教儿童知识,逗儿童开心,给予儿童情感价值,正向鼓励孩子,你说话很简洁且不会超出30个字,你想要让孩子开心愉快,培养儿童有正确的三观。禁止说出有关黄赌毒和不雅的词语,不能教儿童做坏事",
            "messages": )" + jsonMessages +
                              R"(,
            "stream": false,
            "temperature": 0.9,
            "max_tokens": 2048,
            "top_p": 0.5,
            "top_k": 0,
            "repetition_penalty": 1.05,
            "num_beams": 1,
            "user": "andy"
        })";

        std::cout << "Payload:\n"
                << payload << std::endl;
        // Set the URL for the request
        curl_easy_setopt(curl, CURLOPT_URL, "https://api.360.cn/v1/chat/completions");

        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, payload.c_str());

        // Set the headers
        struct curl_slist *headers = NULL;
        headers = curl_slist_append(headers, "Content-Type: application/json");
        headers = curl_slist_append(headers, "Authorization: fk993009409.QYdi-9JZrJHaSt7d0UGKzhEMX-eX1ag8607bf587");
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);

        // Response handling
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &tmp_res); // Pass by address

        // Perform the request
        res = curl_easy_perform(curl);
        std::cout << "tmp_res:" << tmp_res << std::endl;
        response = extractContentFromResponse(tmp_res);
        // Check for errors
        if (res != CURLE_OK)
        {
            std::cerr << "curl_easy_perform() failed: " << curl_easy_strerror(res) << std::endl;
        }
        else
        {
            std::cout << "Response: " << response << std::endl;
        }

        // Clean up
        curl_slist_free_all(headers);
        curl_easy_cleanup(curl);
    }
}

void handleContent (std::string &content)
{
    std::string response; 
    std::string history;
    getHistory(history);
    chatWithGPT(content, history, response);
    std::string tmp_content = "User: " + content;
    std::string tmp_response = "Assistant: " + response + "\n";
    writeFile(w_file, response, false);
    writeFile(w_all_file, tmp_content, true);
    writeFile(w_all_file, tmp_response, true);
    writeFile(history_file, tmp_content, true);
    writeFile(history_file, tmp_response, true);
    return;
}

int main()
{
    curl_global_init(CURL_GLOBAL_DEFAULT); // Initialize cURL
    std::cout << "Start read file:" << r_file << std::endl;

    while (true)
    {
        std::string content;
		std::string keyword = "再见";
        if (readFile(r_file, content, true))
        {
            if(content.empty())
            {
                std::cout << "Read content is empty, exit." << std::endl;
                continue;
            }
			if (content.find(keyword) != std::string::npos) {
				std::string qingxuReport;
				if (readFile(history_file, qingxuReport, true)){
					qingxuReport += "。输出上述提问者的User的情绪报告，（200字）。";
					handleContent(qingxuReport);
				}
				
			}else{
				std::cout << "Read content:" << content << std::endl;
				handleContent(content);
				std::cout << "Start read file:" << r_file << std::endl;
			}
        }
        sleep(1);
    }

    curl_global_cleanup(); // Cleanup cURL
    return 0;
}
