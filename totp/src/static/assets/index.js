
 import { http } from './request.js'
 import { initVault } from './vault.js'

const base = document.getElementById('base-url').getAttribute('href');
const baseURL = base.endsWith('/') ? base : base + '/';

const vaultEnabled = window.VAULT_ENABLED === true;
const vaultBase = baseURL + 'vault';

// ============ Tab 切换 ============
const tabTotp = document.getElementById('tab-totp');
const tabVault = document.getElementById('tab-vault');
const viewTotp = document.getElementById('view-totp');
const viewVault = document.getElementById('view-vault');

if (!vaultEnabled) {
    tabVault.remove();
} else {
    tabVault.hidden = false;
}

function switch_tab(name){
    const isTotp = name === 'totp';
    viewTotp.hidden = !isTotp;
    viewVault.hidden = isTotp;
    tabTotp.classList.toggle('active', isTotp);
    tabVault.classList.toggle('active', !isTotp);
}

tabTotp.addEventListener('click', () => switch_tab('totp'));
tabVault.addEventListener('click', () => switch_tab('vault'));

// ============ TOTP 视图 ============
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
        messageArea.textContent = response.msg;
    }
}

// 检测当前登录状态
let result = await http.get(baseURL + "login")
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
let arg1 = 0;
if(login_status){
    // 1. 创建 URLSearchParams 对象. 获取当前完整的查询字符串 (?arg1=...&arg2=...)
    const urlParams = new URLSearchParams(window.location.search);
    console.log("URLSearchParams=", urlParams);

    // 2. 获取特定参数值
    arg1 = urlParams.get('all');
    console.log("拿到url里的参数信息：", arg1);

    if(arg1 == 1){
        label_query(await http.get(baseURL + 'totpall'));
    }
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

    if(arg1 == 1){
        label_query(await http.get(baseURL + 'totpall'));
        return;
    }

    // 2. 此时浏览器已经完成了原生验证 (如 required)
    // 如果验证失败，代码根本不会运行到这里

    // 可选：简单的客户端验证
    if (Value) {
        prevValue = Value;
    }else{
        if(prevValue){
            label_query(await http.post(baseURL + 'totp', {label: prevValue}));
        }
        return;
    }

    // UI 反馈：提交中，禁用按钮防止重复点击
    const originalBtnText = submitBtn.textContent;
    submitBtn.disabled = true;

    try {
        // 使用 request.js 发送请求
        // 如果已经是登录的。直接直接到查询页面。
        if(login_status){
            label_query(await http.post(baseURL + 'totp', {label: Value}));
        }else{
            const r = await http.post(baseURL + 'login', {password: Value});

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

// ============ 密码库视图 ============
if (vaultEnabled) {
    initVault(vaultBase);
}
