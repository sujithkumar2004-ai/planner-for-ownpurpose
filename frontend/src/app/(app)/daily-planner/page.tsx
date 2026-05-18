"use client";

import { useState } from "react";
import useSWR from "swr";
import { apiFetch, LifeTask, TaskStatus } from "@/lib/api";
import { Check, Clock, Play, MoreVertical, Plus, CheckCircle2, Loader2, X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

export default function DailyPlannerPage() {
  const [isAdding, setIsAdding] = useState(false);
  const [newTaskTitle, setNewTaskTitle] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const today = new Date().toISOString().split("T")[0];
  const { data: tasks, error, mutate } = useSWR<LifeTask[]>(`/life-tasks?date=${today}`, apiFetch);

  const toggleTask = async (task: LifeTask) => {
    const newStatus: TaskStatus = task.status === "completed" ? "pending" : "completed";
    
    // Optimistic update
    mutate(
      tasks?.map(t => t.id === task.id ? { ...t, status: newStatus } : t),
      false
    );

    try {
      await apiFetch(`/life-tasks/${task.id}`, {
        method: "PATCH",
        body: JSON.stringify({ status: newStatus })
      });
      mutate(); // Re-validate
    } catch (e) {
      console.error(e);
      mutate(); // Rollback
    }
  };

  const handleAddTask = async () => {
    if (!newTaskTitle.trim()) return;
    setIsSubmitting(true);
    try {
      await apiFetch("/life-tasks", {
        method: "POST",
        body: JSON.stringify({
          title: newTaskTitle,
          due_date: today,
          status: "pending"
        })
      });
      setNewTaskTitle("");
      setIsAdding(false);
      mutate();
    } catch (e) {
      console.error(e);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (error) return <div className="text-red-400 p-8 text-center bg-red-900/10 rounded-2xl border border-red-500/20">Failed to load tasks.</div>;
  if (!tasks) return <div className="flex justify-center p-12"><Loader2 className="w-8 h-8 text-purple-500 animate-spin" /></div>;

  const activeTaskIndex = tasks.findIndex(t => t.status === "active" || t.status === "pending");
  const isAllDone = tasks.length > 0 && tasks.every(t => t.status === "completed");

  return (
    <div className="grid gap-8 max-w-4xl mx-auto py-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Daily Execution</h1>
          <p className="text-sm text-zinc-400 mt-1">Focus on one thing at a time.</p>
        </div>
        <button 
          onClick={() => setIsAdding(true)}
          className="flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/15 text-white rounded-lg text-sm font-medium transition-colors border border-white/5"
        >
          <Plus className="h-4 w-4" />
          Add Task
        </button>
      </div>

      <div className="grid gap-6">
        <div className="relative border-l-2 border-white/10 ml-4 space-y-6 pb-8">
          <AnimatePresence>
            {tasks.map((task, index) => {
              const isActive = index === activeTaskIndex;
              const isPast = task.status === "completed";
              
              return (
                <motion.div 
                  key={task.id}
                  layout
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className={cn(
                    "relative pl-8 transition-all duration-500 group",
                    isPast ? "opacity-60" : "opacity-100"
                  )}
                >
                  {/* Timeline Dot */}
                  <div className={cn(
                    "absolute left-[-9px] top-4 w-4 h-4 rounded-full border-2 transition-colors duration-300 flex items-center justify-center bg-black",
                    isActive ? "border-purple-500 shadow-[0_0_15px_rgba(168,85,247,0.6)] scale-125" : 
                    isPast ? "border-blue-500 bg-blue-500" : "border-white/20"
                  )}>
                    {isPast && <Check className="h-2.5 w-2.5 text-white" />}
                  </div>

                  {/* Task Card */}
                  <div 
                    onClick={() => toggleTask(task)}
                    className={cn(
                      "rounded-2xl border p-5 cursor-pointer transition-all duration-300 backdrop-blur-md",
                      isActive 
                        ? "border-purple-500/50 bg-purple-500/10 shadow-[0_4px_30px_rgba(168,85,247,0.15)]" 
                        : "border-white/5 bg-white/5 hover:bg-white/10 hover:border-white/10"
                    )}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0 flex items-center gap-4">
                        <div className="flex items-center justify-center relative shrink-0">
                          <input 
                            type="checkbox" 
                            checked={task.status === "completed"}
                            onChange={() => {}} // handled by parent div click
                            className="peer h-6 w-6 appearance-none rounded-full border border-white/20 bg-black/50 checked:bg-blue-500 checked:border-blue-500 transition-all cursor-pointer shadow-inner" 
                          />
                          <Check className="h-3.5 w-3.5 text-white absolute pointer-events-none opacity-0 peer-checked:opacity-100 transition-opacity" />
                        </div>
                        
                        <div>
                          <h3 className={cn(
                            "text-lg font-semibold transition-all duration-300",
                            isPast ? "text-zinc-500 line-through decoration-zinc-600" : "text-zinc-100",
                            isActive ? "text-purple-100" : ""
                          )}>
                            {task.title}
                          </h3>
                          <div className="flex items-center gap-3 mt-1.5 text-xs font-medium text-zinc-500 uppercase tracking-widest">
                            <span className="flex items-center gap-1.5">
                              <Clock className="h-3.5 w-3.5" />
                              {task.estimated_minutes ? `${task.estimated_minutes} min` : 'Unestimated'}
                            </span>
                            {isActive && (
                              <span className="flex items-center gap-1 text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded-sm">
                                <Play className="h-3 w-3 fill-current" />
                                Active
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      
                      <button className="text-zinc-500 hover:text-zinc-300 opacity-0 group-hover:opacity-100 transition-opacity p-2">
                        <MoreVertical className="h-5 w-5" />
                      </button>
                    </div>
                  </div>
                </motion.div>
              );
            })}
            
            {isAdding && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="relative pl-8"
              >
                <div className="rounded-2xl border border-white/20 bg-black/40 p-5">
                  <div className="flex items-center gap-3">
                    <input 
                      autoFocus
                      type="text" 
                      placeholder="What needs to be done?" 
                      value={newTaskTitle}
                      onChange={e => setNewTaskTitle(e.target.value)}
                      onKeyDown={e => e.key === "Enter" && handleAddTask()}
                      className="flex-1 bg-transparent border-none outline-none text-white placeholder-zinc-500 text-lg"
                    />
                    <button 
                      onClick={() => setIsAdding(false)}
                      className="p-2 hover:bg-white/10 rounded-full text-zinc-400 hover:text-white"
                    >
                      <X className="w-5 h-5" />
                    </button>
                    <button 
                      onClick={handleAddTask}
                      disabled={!newTaskTitle.trim() || isSubmitting}
                      className="px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition-colors"
                    >
                      {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : "Save"}
                    </button>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
        
        {tasks.length === 0 && !isAdding && (
          <div className="text-center py-12 px-4 rounded-3xl border border-dashed border-white/10 bg-white/5">
            <p className="text-zinc-500 mb-4">No tasks scheduled for today.</p>
            <button 
              onClick={() => setIsAdding(true)}
              className="text-purple-400 font-medium hover:text-purple-300 transition-colors"
            >
              Add your first task
            </button>
          </div>
        )}

        {isAllDone && (
          <motion.div 
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex flex-col items-center justify-center py-12 px-4 rounded-3xl border border-blue-500/20 bg-blue-500/10"
          >
            <div className="h-20 w-20 rounded-full bg-blue-500/20 flex items-center justify-center mb-6 relative">
              <div className="absolute inset-0 rounded-full border border-blue-500/30 animate-ping" />
              <CheckCircle2 className="h-10 w-10 text-blue-400" />
            </div>
            <h3 className="text-2xl font-bold text-white mb-2">Day Complete!</h3>
            <p className="text-zinc-400 text-center max-w-sm">
              You've successfully finished all your planned tasks for today. Outstanding work!
            </p>
          </motion.div>
        )}
      </div>
    </div>
  );
}
