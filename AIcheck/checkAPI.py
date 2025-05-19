from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from AIcheck.ai_check import AIAuditor

# 定义 Pydantic 模型
class SMSRequest(BaseModel):
    signature: str
    content: str
    business_type: str
    account_type: str  # 保留此字段以维持API兼容性

class SMSResponse(BaseModel):
    passed: Optional[bool]
    status: str  # '通过', '驳回'
    business_reason: str
    score: Optional[float] = None

class BatchSMSRequest(BaseModel):
    sms_list: List[SMSRequest]

class BatchSMSResponse(BaseModel):
    results: List[SMSResponse]
    statistics: Dict[str, int]

class SMSChecker:
    def __init__(self):
        # 初始化AI审核器
        self.ai_auditor = AIAuditor()
        
    def check_sms(self, signature: str, content: str, business_type: str, account_type: str) -> SMSResponse:
        """
        审核单条短信
        
        Args:
            signature: 短信签名
            content: 短信内容
            business_type: 业务类型
            account_type: 客户类型（AI审核中暂不使用）
            
        Returns:
            SMSResponse: 审核结果响应对象
        """
        # 调用AI审核方法
        passed, details = self.ai_auditor.audit_sms_with_cache(signature, content, business_type)
        
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
            score=None
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
async def checkAPI_single_sms(request: SMSRequest):
    """
    审核单条短信内容
    """
    checker = SMSChecker()
    result = checker.check_sms(
        request.signature,
        request.content,
        request.business_type,
        request.account_type
    )
    return result

@app.post("/api/v1/batch-check", response_model=BatchSMSResponse)
async def check_batch_sms(request: BatchSMSRequest):
    """
    批量审核多条短信内容
    """
    if len(request.sms_list) == 0:
        raise HTTPException(status_code=400, detail="短信列表不能为空")
        
    checker = SMSChecker()
    results = []
    

# 如果直接运行该文件，启动 API 服务器
if __name__ == "__main__":
    uvicorn.run("checkAPI:app", host="0.0.0.0", port=8000, reload=True)
    