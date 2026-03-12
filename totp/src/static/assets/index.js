// 1. 定义逻辑函数
async function handleGetClick() {
  console.log("按钮被点击了！");
  await request('https://jsonplaceholder.typicode.com/users');
}

// 2. 等待 DOM 加载完成 (防止 JS 运行时按钮还没生成)
document.addEventListener('DOMContentLoaded', function() {
  // 3. 找到按钮元素
  const btn = document.getElementById('btn-get');
  
  if (btn) {
    // 4. 绑定事件监听器
    btn.addEventListener('click', handleGetClick);
    console.log("事件监听已绑定到 #btn-get");
  }
});