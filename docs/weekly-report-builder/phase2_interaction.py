import json
import logging
import os
from typing import Dict, Any, List, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("phase2_interaction")

class Phase2InteractionManager:
    """
    阶段二交互与动态调整模块 (Phase2 Interaction Manager)
    
    功能：
    1. 模块推荐展示器：将 module_extractor.py 的输出格式化为结构化推荐清单，按P0/P1/P2层级展示
    2. 用户选定机制：支持用户勾选/取消模块，以及手动添加未推荐模块
    3. 异常分支D的动态调整流程：用户调整优先级或模块列表时，重新触发优先级评分，循环至用户确认
    4. 阶段二完成状态持久化：保存用户最终选定的模块列表JSON供阶段三使用
    """
    
    def __init__(self, state_dir: str = "./state"):
        self.state_dir = state_dir
        self.sessions = {}
        if not os.path.exists(self.state_dir):
            os.makedirs(self.state_dir)
            
    def load_from_phase1(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        从阶段一持久化文件加载业务架构数据，避免通过上下文传递。
        返回 phase1_final 数据字典；文件不存在时返回 None。
        """
        file_path = os.path.join(self.state_dir, f"{session_id}_phase1_final.json")
        if not os.path.exists(file_path):
            logger.warning(f"阶段一状态文件不存在: {file_path}，请确认 session_id 正确或先完成阶段一。")
            return None
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"会话 {session_id} 已从 {file_path} 加载阶段一状态")
            return data
        except Exception as e:
            logger.error(f"加载阶段一状态失败: {str(e)}")
            return None

    def format_recommendation_result(self, extraction_result: Dict[str, Any]) -> str:
        """
        1. 模块推荐展示器
        将 module_extractor.py 的输出格式化为结构化推荐清单，按P0/P1/P2层级展示
        """
        if "data" not in extraction_result or "recommended_modules" not in extraction_result["data"]:
            return "❌ 模块提炼结果格式错误，无法展示推荐列表。"
            
        modules = extraction_result["data"]["recommended_modules"]
        
        output = "📊 **阶段二：模块提炼与优先级划分结果**\n\n"
        output += "基于第一阶段确认的业务架构，我为您提炼了以下建议在周报网页中呈现的模块：\n\n"
        
        # P0 模块
        p0_modules = [m for m in modules if m.get("priority") == "P0"]
        if p0_modules:
            output += "### 🥇 首屏模块 (P0 - 建议默认展示)\n"
            for m in p0_modules:
                output += f"- [x] **{m['name']}**\n"
                if "intent" in m:
                    output += f"  - 呈现意图: {m['intent']}\n"
                if "score" in m:
                    output += f"  - 推荐指数: {m['score']:.1f}\n"
            output += "\n"
            
        # P1 模块
        p1_modules = [m for m in modules if m.get("priority") == "P1"]
        if p1_modules:
            output += "### 🥈 核心下钻模块 (P1 - 建议作为主要Tab或下钻页面)\n"
            for m in p1_modules:
                output += f"- [x] **{m['name']}**\n"
                if "intent" in m:
                    output += f"  - 呈现意图: {m['intent']}\n"
                if "score" in m:
                    output += f"  - 推荐指数: {m['score']:.1f}\n"
            output += "\n"
            
        # P2 模块
        p2_modules = [m for m in modules if m.get("priority") == "P2"]
        if p2_modules:
            output += "### 🥉 辅助模块 (P2 - 建议放入金刚区或次要入口)\n"
            for m in p2_modules:
                output += f"- [ ] **{m['name']}** (默认未勾选)\n"
                if "intent" in m:
                    output += f"  - 呈现意图: {m['intent']}\n"
                if "score" in m:
                    output += f"  - 推荐指数: {m['score']:.1f}\n"
            output += "\n"
            
        # 行动号召
        output += "---\n"
        
        if extraction_result.get("data", {}).get("data_integrity_warning"):
            output += "⚠️ **数据完整性提示：**\n"
            output += "当前提炼的模块中，可绘制成图表的数据类模块（如漏斗转化、指标趋势矩阵、用户分层气泡图等）较少或完全没有。\n"
            output += "💡 **建议：** 为了丰富周报的可视化呈现，建议您上传更结构化的数据（如 Excel/CSV 文件），以便我们为您生成更直观的数据图表。\n\n"
            
        output += "💡 **请确认以上模块推荐：**\n"
        output += "1. **确认无误**：如果同意上述推荐，请回复“确认”，我们将进入阶段三（组件匹配）。\n"
        output += "2. **需要调整**：您可以回复例如“取消勾选财务情况”、“把团队动态提升为P1”、“新增一个‘竞品分析’模块”。\n"
        
        return output
        
    def start_interaction(self, session_id: str, extraction_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        启动阶段二交互，展示推荐结果并进入等待状态
        """
        formatted_output = self.format_recommendation_result(extraction_result)
        
        # 初始化会话状态，默认勾选 P0 和 P1
        modules = extraction_result.get("data", {}).get("recommended_modules", [])
        selected_modules = [m for m in modules if m.get("priority") in ["P0", "P1"]]
        unselected_modules = [m for m in modules if m.get("priority") == "P2"]
        
        self.sessions[session_id] = {
            "status": "waiting_for_confirmation",
            "original_extraction": extraction_result,
            "current_modules": modules,
            "selected_modules": selected_modules,
            "unselected_modules": unselected_modules,
            "history": [modules]
        }
        
        logger.info(f"会话 {session_id} 进入阶段二等待确认状态")
        
        return {
            "status": "waiting",
            "message": formatted_output,
            "session_id": session_id
        }
        
    def process_user_feedback(self, session_id: str, user_feedback: str, llm_updater_func=None) -> Dict[str, Any]:
        """
        3. 异常分支D的动态调整流程：处理用户对模块列表或优先级的调整
        
        参数:
        - session_id: 会话ID
        - user_feedback: 用户的反馈文本
        - llm_updater_func: 回调函数，接收(当前模块列表, 用户反馈)，返回更新后的模块列表。
                            在实际应用中，这里会调用LLM解析用户意图并更新模块列表，
                            甚至可能重新调用 ModuleExtractor 的评分逻辑。
        """
        if session_id not in self.sessions:
            return {"status": "error", "message": "未找到对应的会话，请重新开始阶段二。"}
            
        session = self.sessions[session_id]
        
        # 检查是否是确认指令
        confirm_keywords = ["确认", "无误", "没问题", "ok", "yes", "继续", "同意"]
        is_confirm = any(user_feedback.strip().lower() == kw for kw in confirm_keywords) or \
                     (len(user_feedback) < 10 and any(kw in user_feedback.lower() for kw in confirm_keywords))
                     
        if is_confirm:
            # 用户确认，进入持久化流程
            return self.finalize_phase2(session_id)
            
        # 用户提出修改，触发异常分支D的动态调整流程
        logger.info(f"会话 {session_id} 触发阶段二动态调整流程，用户反馈: {user_feedback[:50]}...")
        
        if llm_updater_func:
            try:
                # 调用外部更新逻辑（通常是LLM解析意图并更新列表）
                updated_modules = llm_updater_func(session["current_modules"], user_feedback)
                
                # 更新会话状态
                session["history"].append(session["current_modules"])
                session["current_modules"] = updated_modules
                
                # 重新构建 extraction_result 格式以复用格式化函数
                updated_extraction = {
                    "data": {
                        "recommended_modules": updated_modules
                    }
                }
                
                # 重新格式化输出
                formatted_output = self.format_recommendation_result(updated_extraction)
                
                return {
                    "status": "waiting",
                    "message": "🔄 **已根据您的反馈调整了模块列表与优先级：**\n\n" + formatted_output,
                    "session_id": session_id
                }
            except Exception as e:
                logger.error(f"更新模块列表失败: {str(e)}")
                return {
                    "status": "error",
                    "message": f"调整模块时发生错误: {str(e)}。请重试或换种说法。"
                }
        else:
            # 如果没有提供更新函数，返回提示（仅用于测试或占位）
            return {
                "status": "error",
                "message": "未提供模块更新处理函数，无法应用调整。"
            }
            
    def finalize_phase2(self, session_id: str) -> Dict[str, Any]:
        """
        4. 阶段二完成状态持久化：保存用户最终选定的模块列表JSON供阶段三使用
        """
        if session_id not in self.sessions:
            return {"status": "error", "message": "未找到对应的会话。"}
            
        session = self.sessions[session_id]
        
        # 提取最终选定的模块（假设 current_modules 中包含了所有用户期望保留的模块，
        # 实际逻辑中可能需要根据 selected 状态过滤，这里简化为保存所有 current_modules，
        # 并在其中标记状态，或者由 llm_updater_func 确保 current_modules 就是最终列表）
        final_modules = session["current_modules"]
        
        final_data = {
            "session_id": session_id,
            "phase": 2,
            "status": "completed",
            "selected_modules": final_modules
        }
        
        # 持久化到文件
        file_path = os.path.join(self.state_dir, f"{session_id}_phase2_final.json")
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, ensure_ascii=False, indent=2)
                
            session["status"] = "completed"
            logger.info(f"会话 {session_id} 阶段二完成，状态已持久化至 {file_path}")
            
            return {
                "status": "completed",
                "message": "✅ **阶段二确认完成！** 模块列表与优先级已保存。\n\n接下来我们将进入**阶段三：组件匹配与布局生成**。",
                "data_path": file_path,
                "data": final_data
            }
        except Exception as e:
            logger.error(f"持久化状态失败: {str(e)}")
            return {
                "status": "error",
                "message": f"保存状态时发生错误: {str(e)}"
            }

# 简单测试代码
if __name__ == "__main__":
    manager = Phase2InteractionManager(state_dir="./test_state")
    
    # 模拟 module_extractor.py 的输出
    mock_extraction = {
        "status": "success",
        "data": {
            "recommended_modules": [
                {"name": "项目健康度诊断 (Health Score)", "priority": "P0", "score": 90.0, "intent": "首屏核心展示：综合评分"},
                {"name": "KPI 监控与数据异常", "priority": "P0", "score": 85.0, "intent": "首屏核心展示：关键业务指标红绿灯"},
                {"name": "业务模块详情 (Module Details)", "priority": "P1", "score": 65.0, "intent": "下钻/辅助展示：各子业务线具体进展"},
                {"name": "风险与问题登记册", "priority": "P1", "score": 60.0, "intent": "下钻/辅助展示：阻塞问题、潜在风险点"},
                {"name": "团队构成与动态", "priority": "P2", "score": 45.0, "intent": "下钻/辅助展示：人员变动、招聘需求"}
            ]
        }
    }
    
    print("--- 1. 启动交互 ---")
    result1 = manager.start_interaction("session_002", mock_extraction)
    print(result1["message"])
    
    print("\n--- 2. 模拟用户反馈修改 (异常分支D) ---")
    # 模拟一个简单的更新函数：将团队动态提升为P1，并新增竞品分析
    def mock_updater(current_modules, feedback):
        new_modules = current_modules.copy()
        for m in new_modules:
            if "团队" in m["name"]:
                m["priority"] = "P1"
                m["score"] = 70.0
        new_modules.append({
            "name": "竞品分析 (Competitor Analysis)",
            "priority": "P1",
            "score": 68.0,
            "intent": "下钻/辅助展示：竞品动态与对比"
        })
        # 重新排序
        new_modules.sort(key=lambda x: x.get("score", 0), reverse=True)
        return new_modules
        
    result2 = manager.process_user_feedback("session_002", "把团队动态提升为P1，并新增一个竞品分析模块", mock_updater)
    print(result2["message"])
    
    print("\n--- 3. 模拟用户确认 ---")
    result3 = manager.process_user_feedback("session_002", "确认无误")
    print(result3["message"])
    print(f"保存路径: {result3.get('data_path')}")
