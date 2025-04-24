from 规则审核.business import validate_business
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import re
import uvicorn

# 定义 Pydantic 模型
class SMSRequest(BaseModel):
    signature: str
    content: str
    business_type: str
    account_type: str

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
    def check_sms(self, signature: str, content: str, business_type: str, account_type: str) -> SMSResponse:
        """
        审核单条短信
        
        Args:
            signature: 短信签名
            content: 短信内容
            business_type: 业务类型
            account_type: 客户类型
            
        Returns:
            SMSResponse: 审核结果响应对象
        """
        # 业务类型审核（包含客户类型审核）
        business_passed, business_reason = validate_business(business_type, content, signature, account_type)
        
        # 初始化响应对象
        response = SMSResponse(
            passed=business_passed, 
            status="通过" if business_passed else "驳回",
            business_reason=business_reason,
            score=None
        )
        
        # 从审核结果中提取分数
        try:
            # 使用正则表达式提取分数
            score_match = re.search(r'总分: (\d+\.?\d*)', business_reason)
            if not score_match:
                score_match = re.search(r'最终得分: (\d+\.?\d*)', business_reason)
                
            if score_match:
                score = float(score_match.group(1))
                response.score = score
                
        except Exception as e:
            print(f"提取分数时出错: {str(e)}")
            
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
    
    # 统计计数器
    passed_count = 0
    rejected_count = 0
    manual_count = 0
    
    for sms in request.sms_list:
        result = checker.check_sms(
            sms.signature,
            sms.content,
            sms.business_type,
            sms.account_type
        )
        
        # 统计结果
        if result.passed is None:
            manual_count += 1
        elif result.passed:
            passed_count += 1
        else:
            rejected_count += 1
            
        results.append(result)
    
    # 返回批量结果和统计数据
    return BatchSMSResponse(
        results=results,
        statistics={
            "total": len(results),
            "passed": passed_count,
            "rejected": rejected_count,
            "manual_review": manual_count
        }
    )

# 如果直接运行该文件，启动 API 服务器
if __name__ == "__main__":
    uvicorn.run("checkAPI:app", host="0.0.0.0", port=8000, reload=True)
    