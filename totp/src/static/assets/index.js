
 import { http, configure } from './request.js'

const div_display = document.getElementById('display');

const form = document.getElementById('input-form');
const Input = document.getElementById('input-value');
const messageArea = document.getElementById('message-area');
const submitBtn = document.getElementById('submit-btn');

const totp_list = document.getElementById('totp-result-list');

function change_login(){
    messageArea.textContent = '需要登录';
    document.getElementById('input-label').textContent = "密码";
    document.getElementById('input-value').type = "password";
    document.getElementById('input-value').placeholder = "请输入密码";
}

function change_query(){
    messageArea.style.color = "green";
    messageArea.textContent = '输入查询名称';
    document.getElementById('input-label').textContent = "名称";
    document.getElementById('input-value').type = "text";
    document.getElementById('input-value').placeholder = "请输入名称";
}

// 请查询
async function label_query(response){
    
    console.log(response)

    let totps = response.data
    // 处理空数据情况
    if (!totps || totps.length === 0) {
        messageArea.innerText = '暂无数据';
        totp_list.innerHTML = '';

    }else{
        // 使用反引号 ` 包裹模板字符串，${} 中插入变量
        const htmlList = totps.map(totp => `
            <br><label>${totp.label} 动态密码：${totp.pw} 剩下时间：${totp.time_left}</label></></br>
        `);

        // 4. 拼接并一次性写入 DOM
        // join('') 把数组变成一个大字符串
        totp_list.innerHTML = htmlList.join('');
        messageArea.textContent = '输入查询名称';
    }
}

// 为http 配置  baseURL
const path = window.location.pathname;
console.log("当前是那个路径：", path);
configure({baseURL: path});


// 检测当前登录状态
let result = await http.get("login")
let login_status = false;

if(result.code == 0){
    login_status = true;
    //说明已经是登录的
    // 切换到 登录提示
    change_query();
}else{
    change_login();
}

// 先处理 直接 填写URL 访问的情况
if(window.Location.pathname == path + "/all" && login_status){
    label_query(await http.post('totpall', {label: Value}));
}


let prevValue = '';
// 定义表单按钮函数
async function submit_eventListener(event){
    // 🔴 关键步骤：阻止表单默认的提交行为（防止页面刷新跳转）
    event.preventDefault();

    // 获取用户输入的值
    const Value = Input.value;
    Input.value = ''; // 拿到之后清理
    console.log("Value：", Value, "prevValse", prevValue);

    // 2. 此时浏览器已经完成了原生验证 (如 required)
    // 如果验证失败，代码根本不会运行到这里

    // // 可选：简单的客户端验证
    if (Value) {
        prevValue = Value;

        // if(login_status){
        //     messageArea.textContent = "名称不能为空";
        // }else{
        //     messageArea.textContent = "密码不能为空";
        // }

    }else{

        if(prevValue){
            label_query(await http.post('totp', {label: prevValue}));
        }
        return;
    }

    // UI 反馈：提交中，禁用按钮防止重复点击
    const originalBtnText = submitBtn.textContent;
    submitBtn.disabled = true;

    try {
        // 3. 使用 request.js 发送请求
        // 假设你的库支持 post(url, data) 语法
        // 后端接口路径根据你的实际情况修改，例如 'api/login'
        
        // 如果已经是登录的。直接直接到查询页面。
        if(login_status){
            label_query(await http.post('totp', {label: Value}));
        }else{
            const r = await http.post('login', {password: Value});
            // 如果后端需要 username，也可以在这里添加: username: 'admin'

            // 4. 处理成功响应
            if(r.code == 0){
                console.log(r);
                login_status = true;
                change_query();
            }else{
                console.log(r);
                login_status = false;
                messageArea.style.color = "red";
                messageArea.textContent = r.msg;
            }
        }
 
        // 可以在这里执行跳转或保存 Token
        // window.location.href = '/dashboard'; 
        // 或者 localStorage.setItem('token', response.token);

        submitBtn.disabled = false;

    } catch (error) {
        // 5. 处理错误响应
        console.error('登录失败:', error);
        
        messageArea.style.color = "red";
        // 显示后端返回的错误信息，或者默认错误提示
        messageArea.textContent = "❌ 登录失败: " + (error.message || "密码错误或网络异常");
        
        // 重置按钮状态
        submitBtn.textContent = originalBtnText;
        submitBtn.disabled = false;
      }
};

// 2. 监听表单的 submit 事件
form.addEventListener('submit', submit_eventListener);