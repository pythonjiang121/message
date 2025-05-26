import asyncio
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import uvicorn
from ai_check import AIAuditor
from loguru import logger

# 定义 Pydantic 模型
class SMSRequest(BaseModel):
    signature: str
    content: str
    business_type: str

class SMSResponse(BaseModel):
    passed: Optional[bool]
    status: str  # '通过', '驳回'
    business_reason: str

class BatchSMSRequest(BaseModel):
    sms_list: List[SMSRequest]

class BatchSMSResponse(BaseModel):
    results: List[SMSResponse]
    statistics: Dict[str, int]

class APIUsageResponse(BaseModel):
    api_balance: Dict
    token_usage: Dict
    status: str

class APIBalanceResponse(BaseModel):
    balance: Optional[float]
    balance_info: Dict
    status: str
    message: str

class SMSChecker:
    def __init__(self):
        # 初始化AI审核器
        self.ai_auditor = AIAuditor()
        
    def check_sms(self, signature: str, content: str, business_type: str) -> SMSResponse:
        """
        审核单条短信
        
        Args:
            signature: 短信签名
            content: 短信内容
            business_type: 业务类型
            
        Returns:
            SMSResponse: 审核结果响应对象
        """
        # 调用AI审核方法
        passed, details = self.ai_auditor.audit_sms(signature, content, business_type)
        
        # 构建原因说明
        if not passed and "reasons" in details:
            business_reason = "; ".join(details["reasons"])
        elif not passed and "error" in details:
            business_reason = f"审核错误: {details['error']}"
        else:
            business_reason = "内容符合规范"
        
        # 初始化响应对象
        response = SMSResponse(
            passed=passed, 
            status="通过" if passed else "驳回",
            business_reason=business_reason,
        )

        return response
        
    def get_api_usage(self) -> APIUsageResponse:
        """
        获取API使用情况
        
        Returns:
            APIUsageResponse: API使用情况响应对象
        """
        # 获取API余额信息
        api_balance = self.ai_auditor.check_api_balance()
        
        # 获取token使用统计
        token_usage = self.ai_auditor.get_token_usage_stats()
        
        # 初始化响应对象
        response = APIUsageResponse(
            api_balance=api_balance,
            token_usage=token_usage,
            status="成功" if "error" not in api_balance else "失败"
        )
        
        return response
        
    def get_api_balance(self) -> APIBalanceResponse:
        """
        获取DeepSeek API余额信息
        
        Returns:
            APIBalanceResponse: API余额信息响应对象
        """
        # 获取API余额信息
        balance_info = self.ai_auditor.check_api_balance()
        
        # 提取余额
        balance = None
        message = "获取余额成功"
        currency = "CNY"
        
        if "error" not in balance_info:
            try:
                # 根据DeepSeek API文档的格式解析
                if "is_available" in balance_info and "balance_infos" in balance_info:
                    if balance_info["is_available"] and len(balance_info["balance_infos"]) > 0:
                        # 遍历找到人民币余额
                        for balance_data in balance_info["balance_infos"]:
                            if balance_data["currency"] == "CNY":
                                currency = "CNY"
                                
                                # 获取总余额
                                if "total_balance" in balance_data:
                                    balance = float(balance_data["total_balance"])
                                    logger.info(f"人民币余额: ¥{balance:.2f}")
                                    break
            except (KeyError, ValueError) as e:
                message = f"解析余额信息出错: {str(e)}"
        else:
            message = balance_info.get("error", "未知错误")
        
        # 初始化响应对象
        response = APIBalanceResponse(
            balance=balance,
            balance_info=balance_info,
            status="成功" if balance is not None else "失败",
            message=message
        )
        
        return response

# 创建 FastAPI 应用
app = FastAPI(
    title="短信审核 API",
    description="提供短信内容合规性审核的 RESTful API 服务",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {"message": "欢迎使用短信审核 API 服务"}

@app.post("/api/v1/check", response_model=SMSResponse)
async def checkAPI_single_sms(request: SMSRequest, request_info: Request):
    """
    审核单条短信内容
    """
    logger.info(f"开始审核单条短信: {request.signature} - {request.content}")
    checker = SMSChecker()

    try:
        # 获取客户端信息
        client_host = request_info.client.host if request_info.client else "未知客户端"
        client_info = f"客户端IP: {client_host}"
        logger.info(f"接收到来自 {client_info} 的审核请求")
        
        # 创建一个任务来监控客户端连接状态
        async def check_connection():
            while True:
                await asyncio.sleep(1)
                # 如果客户端已断开连接，则取消审核任务
                if not request_info.client or await request_info.is_disconnected():
                    logger.warning(f"客户端 {client_host} 已断开连接，终止审核任务")
                    return True
                
        
        # 创建审核任务
        audit_task = asyncio.create_task(asyncio.to_thread(
            checker.check_sms,
            request.signature,
            request.content,
            request.business_type
        ))
        
        # 创建连接监控任务
        connection_task = asyncio.create_task(check_connection())
        
        # 等待任一任务完成
        done, pending = await asyncio.wait(
            [audit_task, connection_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # 取消未完成的任务
        for task in pending:
            task.cancel()
        
        # 如果是连接监控任务先完成，说明客户端已断开
        if connection_task in done and await connection_task:
            raise asyncio.CancelledError("客户端已断开连接")
        
        # 获取审核结果
        result = await audit_task
        logger.info(f"审核结果: {result}")
        return result
    except asyncio.CancelledError as e:
        logger.warning(f"审核任务已取消: {str(e)}")
        return SMSResponse(
            passed=False,
            status="已取消",
            business_reason="客户端已断开连接，审核任务已取消"
        )
    except Exception as e:
        logger.error(f"审核过程中发生错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/usage", response_model=APIUsageResponse)
async def get_api_usage(request_info: Request):
    """
    获取API使用情况
    """
    logger.info("开始获取API使用情况")
    checker = SMSChecker()

    try:
        # 获取客户端信息
        client_host = request_info.client.host if request_info.client else "未知客户端"
        client_info = f"客户端IP: {client_host}"
        logger.info(f"接收到来自 {client_info} 的API使用情况请求")
        
        # 获取API使用情况
        result = checker.get_api_usage()
        logger.info(f"API使用情况获取成功")
        return result
    except Exception as e:
        logger.error(f"获取API使用情况过程中发生错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


    
# 如果直接运行该文件，启动 API 服务器
if __name__ == "__main__":
    uvicorn.run("checkAPI:app", host="0.0.0.0", port=8000, reload=True)
    