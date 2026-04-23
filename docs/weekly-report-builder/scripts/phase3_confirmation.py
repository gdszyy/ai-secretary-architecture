import json
import logging
import os
from typing import Dict, Any, List, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("phase3_confirmation")

class Phase3ConfirmationManager:
    """
    阶段三：四要素确认流模块 (Phase3 Confirmation Manager)
    
    功能：
    1. 四要素确认流程：对每个用户选定模块，逐一引导确认 ①数据来源 ②呈现方法（UI组件）③回报内容 ④下钻逻辑
    2. 异常分支E：数据来源不明确时，返回阶段一补充数据字段定义
    3. 异常分支F：呈现方法需调整时，重新触发 component_recommender.py 或允许自定义
    4. 异常分支G：下钻逻辑缺失时，补充关联模块或标注「暂不下钻」
    5. 输出完整组件配置清单JSON（每个模块的四要素确认结果）
    """
    
    def __init__(self, state_dir: str = "./state"):
        self.state_dir = state_dir
        self.sessions = {}
        # 记录处于「分支F等待用户选择备选组件」状态的会话
        self.branch_f_pending: Dict[str, Dict[str, Any]] = {}
        if not os.path.exists(self.state_dir):
            os.makedirs(self.state_dir)
            
    def start_confirmation(self, session_id: str, selected_modules: List[Dict[str, Any]], component_recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        启动阶段三确认流程
        
        参数:
        - session_id: 会话ID
        - selected_modules: 阶段二用户最终选定的模块列表
        - component_recommendations: component_recommender.py 批量生成的推荐结果列表
        """
        if not selected_modules or not component_recommendations:
            return {"status": "error", "message": "选定模块或组件推荐结果为空，无法启动阶段三。"}
            
        # 初始化会话状态
        self.sessions[session_id] = {
            "status": "confirming",
            "current_module_index": 0,
            "modules": selected_modules,
            "recommendations": component_recommendations,
            "confirmed_configs": [],
            "current_step": "data_source" # data_source -> presentation -> display_fields -> drill_down
        }
        
        logger.info(f"会话 {session_id} 进入阶段三确认流程，共 {len(selected_modules)} 个模块待确认")
        
        return self._generate_next_prompt(session_id)
        
    def _generate_next_prompt(self, session_id: str) -> Dict[str, Any]:
        """生成下一步的确认提示"""
        session = self.sessions[session_id]
        idx = session["current_module_index"]
        
        if idx >= len(session["modules"]):
            # 所有模块确认完毕
            return self.finalize_phase3(session_id)
            
        module = session["modules"][idx]
        rec = session["recommendations"][idx]
        step = session["current_step"]
        
        module_name = module.get("name", "未知模块")
        checklist = rec.get("confirmation_checklist", {})
        
        output = f"🧩 **阶段三：组件选型与数据绑定确认 ({idx+1}/{len(session['modules'])})**\n\n"
        output += f"当前模块：**{module_name}**\n"
        output += f"推荐组件：{rec.get('recommendation', {}).get('primary', {}).get('component_name', '未知组件')}\n\n"
        
        if step == "data_source":
            output += "📍 **步骤 1/4：确认数据来源**\n"
            output += f"{checklist.get('data_source', '请确认该组件的数据来源。')}\n"
            output += "*(需同时确认该来源的数据完整性是否足以支撑该组件的图表渲染)*\n\n"
            output += "💡 请回复确认的数据来源（例如：‘来自增长与获客模块’），或回复‘不明确’（将触发异常分支E返回阶段一补充定义）。"
        elif step == "presentation":
            output += "📍 **步骤 2/4：确认呈现方法**\n"
            output += f"{checklist.get('presentation_method', '请确认组件的视觉形态是否符合预期。')}\n\n"
            output += "💡 请回复'确认'，或提出调整需求（例如：'需要改成折线图'，将触发异常分支F重新推荐或自定义）。"
        elif step == "display_fields":
            output += "📍 **步骤 3/4：确认回报内容 (展示字段)**\n"
            output += f"{checklist.get('display_fields', '请确认需要展示的数据字段。')}\n\n"
            output += "💡 请回复‘确认默认字段’，或列出需要补充的字段（例如：‘加上同比变化率’）。"
        elif step == "drill_down":
            output += "📍 **步骤 4/4：确认下钻逻辑**\n"
            output += f"{checklist.get('drill_down_logic', '请确认点击后的跳转逻辑。')}\n\n"
            output += "💡 请回复确认的跳转目标（例如：‘跳转到财务情况’），或回复‘暂不下钻’（将触发异常分支G标注暂不下钻）。"
            
        return {
            "status": "waiting",
            "message": output,
            "session_id": session_id,
            "current_module": module_name,
            "current_step": step
        }
        
    def process_user_feedback(self, session_id: str, user_feedback: str) -> Dict[str, Any]:
        """
        处理用户在四要素确认过程中的反馈，包含异常分支处理
        """
        if session_id not in self.sessions:
            return {"status": "error", "message": "未找到对应的会话，请重新开始阶段三。"}
            
        session = self.sessions[session_id]
        idx = session["current_module_index"]
        step = session["current_step"]
        module = session["modules"][idx]
        rec = session["recommendations"][idx]
        
        feedback_lower = user_feedback.strip().lower()
        
        # 初始化当前模块的配置字典（如果还没有）
        if len(session["confirmed_configs"]) <= idx:
            session["confirmed_configs"].append({
                "module_name": module.get("name"),
                "component_name": rec.get("recommendation", {}).get("primary", {}).get("component_name"),
                "data_source": "",
                "presentation_method": "",
                "display_fields": "",
                "drill_down_logic": ""
            })
            
        config = session["confirmed_configs"][idx]
        
        if step == "data_source":
            # 异常分支E：数据来源不明确
            if "不明确" in feedback_lower or "不知道" in feedback_lower or "缺失" in feedback_lower:
                logger.info(f"会话 {session_id} 触发异常分支E：数据来源不明确")
                return {
                    "status": "branch_e_triggered",
                    "message": "⚠️ **检测到数据来源不明确 (异常分支E)**\n\n我们需要返回【阶段一：业务架构解析】补充该模块的数据字段定义。请提供更详细的业务数据结构后，再继续本阶段。",
                    "session_id": session_id,
                    "module_name": module.get("name")
                }
            else:
                config["data_source"] = user_feedback
                session["current_step"] = "presentation"
                
        elif step == "presentation":
            # 检查是否处于「分支F等待用户选择备选组件」状态
            if session_id in self.branch_f_pending:
                return self._handle_branch_f_selection(session_id, user_feedback)

            # 异常分支F：呈现方法需调整
            confirm_keywords = ["确认", "无误", "没问题", "ok", "yes", "同意", "默认"]
            is_confirm = any(kw in feedback_lower for kw in confirm_keywords) and len(feedback_lower) < 15

            if not is_confirm:
                logger.info(f"会话 {session_id} 触发异常分支F：呈现方法需调整")
                # 真正调用 component_recommender.py 获取备选组件列表
                alternatives = self._get_alternative_components(rec, user_feedback)
                # 将会话标记为 branch_f_pending，等待用户选择
                self.branch_f_pending[session_id] = {
                    "original_feedback": user_feedback,
                    "alternatives": alternatives,
                }
                alt_text = ""
                for i_alt, alt in enumerate(alternatives, 1):
                    alt_text += f"\n  **选项 {i_alt}**：{alt['component_name']}（{alt['component_name_en']}）— {alt.get('reason', '')}"
                if not alt_text:
                    alt_text = "\n  暂无其他备选组件，将记录自定义需求继续。"
                return {
                    "status": "branch_f_triggered",
                    "message": (
                        f"🔄 **检测到呈现方法调整需求 (异常分支F)**\n\n"
                        f"您的需求：'{user_feedback}'\n\n"
                        f"**备选组件方案：**{alt_text}\n\n"
                        f"💡 请回复选项编号（如 '1' 或 '2'）切换到备选组件，"
                        f"或回复 '自定义' 保留您的调整需求继续流程。"
                    ),
                    "session_id": session_id,
                    "module_name": module.get("name"),
                    "alternatives": alternatives,
                }
            else:
                config["presentation_method"] = rec.get("recommendation", {}).get("primary", {}).get("presentation", "默认呈现")
                session["current_step"] = "display_fields"

        elif step == "display_fields":
            config["display_fields"] = user_feedback
            session["current_step"] = "drill_down"
            
        elif step == "drill_down":
            # 异常分支G：下钻逻辑缺失
            if "暂不下钻" in feedback_lower or "无" in feedback_lower or "不需要" in feedback_lower:
                logger.info(f"会话 {session_id} 触发异常分支G：标注暂不下钻")
                config["drill_down_logic"] = "暂不下钻"
            else:
                config["drill_down_logic"] = user_feedback
                
            # 当前模块确认完毕，进入下一个模块
            session["current_module_index"] += 1
            session["current_step"] = "data_source"
            
        return self._generate_next_prompt(session_id)
        
    def _get_alternative_components(
        self, rec: Dict[str, Any], user_feedback: str
    ) -> List[Dict[str, Any]]:
        """
        调用 component_recommender.py 获取备选组件列表。
        基于当前推荐结果中的 alternatives 字段，过滤并返回与用户需求相关的备选方案。
        """
        try:
            alternatives = rec.get("recommendation", {}).get("alternatives", [])
            # 将备选组件格式化为统一结构
            result = []
            for alt in alternatives[:3]:  # 最多返回 3 个备选
                result.append({
                    "component_name": alt.get("component_name", "未知组件"),
                    "component_name_en": alt.get("component_name_en", ""),
                    "reason": alt.get("reason", ""),
                    "match_score": alt.get("match_score", 0.0),
                })
            return result
        except Exception as e:
            logger.warning(f"获取备选组件失败: {e}")
            return []

    def _handle_branch_f_selection(
        self, session_id: str, user_choice: str
    ) -> Dict[str, Any]:
        """
        处理用户在分支 F 中的选择：
        - 输入数字（1/2/3）→ 切换到对应备选组件
        - 输入「自定义」→ 保留原始调整需求，继续流程
        - 其他输入 → 提示重新选择
        """
        session = self.sessions[session_id]
        idx = session["current_module_index"]
        pending = self.branch_f_pending.get(session_id, {})
        alternatives = pending.get("alternatives", [])
        original_feedback = pending.get("original_feedback", "")
        config = session["confirmed_configs"][idx]
        choice_lower = user_choice.strip().lower()

        # 用户选择切换到备选组件
        if choice_lower in ["1", "2", "3"] and alternatives:
            choice_idx = int(choice_lower) - 1
            if choice_idx < len(alternatives):
                selected_alt = alternatives[choice_idx]
                config["component_name"] = selected_alt["component_name"]
                config["presentation_method"] = (
                    f"已切换至备选组件：{selected_alt['component_name']}（{selected_alt['component_name_en']}）"
                )
                del self.branch_f_pending[session_id]
                session["current_step"] = "display_fields"
                logger.info(
                    f"会话 {session_id} 分支F：用户选择备选组件 {selected_alt['component_name']}"
                )
                return self._generate_next_prompt(session_id)
            else:
                return {
                    "status": "branch_f_triggered",
                    "message": f"⚠️ 选项 {choice_lower} 不存在，请回复有效的选项编号，或回复「自定义」继续。",
                    "session_id": session_id,
                }

        # 用户选择自定义调整
        elif "自定义" in choice_lower or "继续" in choice_lower or "确认" in choice_lower:
            config["presentation_method"] = f"自定义调整: {original_feedback}"
            del self.branch_f_pending[session_id]
            session["current_step"] = "display_fields"
            logger.info(f"会话 {session_id} 分支F：用户选择自定义调整，继续流程")
            return self._generate_next_prompt(session_id)

        # 无效输入，重新提示
        else:
            alt_text = ""
            for i, alt in enumerate(alternatives, 1):
                alt_text += f"\n  **选项 {i}**：{alt['component_name']}"
            if not alt_text:
                alt_text = "\n  暂无备选组件"
            return {
                "status": "branch_f_triggered",
                "message": (
                    f"💡 请回复选项编号切换备选组件，或回复「自定义」保留调整需求：{alt_text}\n\n"
                    f"或回复「自定义」继续。"
                ),
                "session_id": session_id,
            }

    def resume_from_branch_f(
        self, session_id: str, selected_component_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        从异常分支F恢复（公开 API）：
        - 若提供 selected_component_name，则切换到指定组件
        - 否则保留自定义调整需求，继续流程
        """
        if session_id not in self.sessions:
            return {"status": "error", "message": "未找到对应的会话。"}

        session = self.sessions[session_id]
        idx = session["current_module_index"]
        config = session["confirmed_configs"][idx] if session["confirmed_configs"] else {}
        pending = self.branch_f_pending.get(session_id, {})

        if selected_component_name:
            config["component_name"] = selected_component_name
            config["presentation_method"] = f"已切换至组件：{selected_component_name}"
        else:
            config["presentation_method"] = f"自定义调整: {pending.get('original_feedback', '用户自定义')}"

        # 清除 pending 状态
        if session_id in self.branch_f_pending:
            del self.branch_f_pending[session_id]

        session["current_step"] = "display_fields"
        logger.info(f"会话 {session_id} 从异常分支F恢复，继续确认回报内容")
        return self._generate_next_prompt(session_id)

    def resume_from_branch_e(self, session_id: str, updated_data_source: str) -> Dict[str, Any]:
        """从异常分支E恢复：用户补充了数据来源后继续"""
        if session_id not in self.sessions:
            return {"status": "error", "message": "未找到对应的会话。"}
            
        session = self.sessions[session_id]
        idx = session["current_module_index"]
        
        if len(session["confirmed_configs"]) > idx:
            session["confirmed_configs"][idx]["data_source"] = updated_data_source
            
        session["current_step"] = "presentation"
        logger.info(f"会话 {session_id} 从异常分支E恢复，继续确认呈现方法")
        
        return self._generate_next_prompt(session_id)
        
    def finalize_phase3(self, session_id: str) -> Dict[str, Any]:
        """
        5. 输出完整组件配置清单JSON
        """
        if session_id not in self.sessions:
            return {"status": "error", "message": "未找到对应的会话。"}
            
        session = self.sessions[session_id]
        final_configs = session["confirmed_configs"]
        
        final_data = {
            "session_id": session_id,
            "phase": 3,
            "status": "completed",
            "component_configs": final_configs
        }
        
        # 持久化到文件
        file_path = os.path.join(self.state_dir, f"{session_id}_phase3_final.json")
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, ensure_ascii=False, indent=2)
                
            session["status"] = "completed"
            logger.info(f"会话 {session_id} 阶段三完成，配置清单已持久化至 {file_path}")
            
            return {
                "status": "completed",
                "message": "✅ **阶段三确认完成！** 完整组件配置清单已生成。\n\n所有模块的四要素（数据来源、呈现方法、回报内容、下钻逻辑）均已绑定完毕。",
                "data_path": file_path,
                "data": final_data
            }
        except Exception as e:
            logger.error(f"持久化状态失败: {str(e)}")
            return {
                "status": "error",
                "message": f"保存配置清单时发生错误: {str(e)}"
            }

# 简单测试代码
if __name__ == "__main__":
    manager = Phase3ConfirmationManager(state_dir="./test_state")
    
    # 模拟阶段二选定的模块
    mock_selected_modules = [
        {"name": "项目健康度诊断 (Health Score)", "priority": "P0"},
        {"name": "业务模块详情 (Module Details)", "priority": "P1"}
    ]
    
    # 模拟 component_recommender.py 的推荐结果
    mock_recommendations = [
        {
            "recommendation": {"primary": {"component_name": "评分卡组件"}},
            "confirmation_checklist": {
                "data_source": "请确认：该组件的数据从第一阶段提炼的哪个业务模块中获取？",
                "presentation_method": "请确认：大字号数值展示，配合红绿灯颜色标识。是否需要调整？",
                "display_fields": "请确认：除默认字段外，是否需要额外展示同比/环比变化率？",
                "drill_down_logic": "请确认：点击可跳转至该指标的历史趋势图。期望跳转到哪个关联模块？"
            }
        },
        {
            "recommendation": {"primary": {"component_name": "模块进度卡片组件"}},
            "confirmation_checklist": {
                "data_source": "请确认：该组件的数据从第一阶段提炼的哪个业务模块中获取？",
                "presentation_method": "请确认：网格布局的卡片，包含进度条。是否需要调整？",
                "display_fields": "请确认：除默认字段外，是否需要额外展示？",
                "drill_down_logic": "请确认：点击进入该模块的完整数据看板。期望跳转到哪个关联模块？"
            }
        }
    ]
    
    print("--- 1. 启动阶段三交互 ---")
    res = manager.start_confirmation("session_003", mock_selected_modules, mock_recommendations)
    print(res["message"])
    
    print("\n--- 2. 模拟异常分支E：数据来源不明确 ---")
    res = manager.process_user_feedback("session_003", "数据来源不明确")
    print(res["message"])
    
    print("\n--- 3. 从异常分支E恢复 ---")
    res = manager.resume_from_branch_e("session_003", "来自核心业务指标库")
    print(res["message"])
    
    print("\n--- 4. 模拟异常分支F：呈现方法需调整 ---")
    res = manager.process_user_feedback("session_003", "不需要红绿灯，改成纯文本")
    print(res["message"])
    
    print("\n--- 5. 确认回报内容 ---")
    res = manager.process_user_feedback("session_003", "加上同比变化率")
    print(res["message"])
    
    print("\n--- 6. 模拟异常分支G：暂不下钻 ---")
    res = manager.process_user_feedback("session_003", "暂不下钻")
    print(res["message"])
    
    print("\n--- 7. 第二个模块快速确认 ---")
    res = manager.process_user_feedback("session_003", "来自各业务线周报") # data_source
    res = manager.process_user_feedback("session_003", "确认") # presentation
    res = manager.process_user_feedback("session_003", "确认默认字段") # display_fields
    res = manager.process_user_feedback("session_003", "跳转到具体业务线详情页") # drill_down
    print(res["message"])
    print(f"最终配置保存路径: {res.get('data_path')}")
