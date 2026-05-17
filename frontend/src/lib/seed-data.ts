import type { Dashboard, Task, Warning } from "@/lib/api";

export const fixedTasks: Task[] = [
  { id: 1, task_date: "2026-05-17", title: "Exam Common Foundation", category: "exam_foundation", start_time: "07:00", end_time: "09:30", completed: true },
  { id: 2, task_date: "2026-05-17", title: "Backend Engineering", category: "backend", start_time: "10:00", end_time: "13:00", completed: false },
  { id: 3, task_date: "2026-05-17", title: "LLM / Agentic AI", category: "llm_agentic_ai", start_time: "14:00", end_time: "17:00", completed: false },
  { id: 4, task_date: "2026-05-17", title: "Gym", category: "gym", start_time: "17:30", end_time: "18:30", completed: false },
  { id: 5, task_date: "2026-05-17", title: "Specialized Exam Rotation", category: "exam_rotation", start_time: "18:30", end_time: "20:30", completed: false },
  { id: 6, task_date: "2026-05-17", title: "Revision / Light Study", category: "revision", start_time: "21:15", end_time: "22:45", completed: true },
  { id: 7, task_date: "2026-05-17", title: "Planning / Journal", category: "journal", start_time: "22:45", end_time: "23:15", completed: false }
];

export const warnings: Warning[] = [
  { id: 1, rule_code: "daily_below_60", level: "YELLOW", message: "Daily completion is below 60%.", active: true, created_at: new Date().toISOString() },
  { id: 2, rule_code: "topic_backlog_25", level: "RED", message: "Exam topic backlog above 25%.", active: true, created_at: new Date().toISOString() }
];

export const dashboard: Dashboard = {
  name: "Life OS",
  daily_completion: 42,
  tasks: fixedTasks,
  warnings,
  exams: [
    { id: 1, name: "CAT 2026", exam_date: "2026-11-29", days_left: 196, progress: 18 },
    { id: 2, name: "GATE DA", exam_date: "2026-02-08", days_left: 0, progress: 22 },
    { id: 3, name: "GATE Mechanical", exam_date: "2026-02-08", days_left: 0, progress: 14 },
    { id: 4, name: "IIT JAM Maths", exam_date: "2026-02-15", days_left: 0, progress: 19 },
    { id: 5, name: "IIT JAM Physics", exam_date: "2026-02-15", days_left: 0, progress: 16 }
  ],
  roadmap: [
    ...["FastAPI", "Express.js", "SQL", "SQLAlchemy", "Sequelize", "JWT auth", "Redis", "Docker", "queues", "system design", "deployment"].map((name) => ({ name, track: "backend", status: "planned" })),
    ...["Prompting", "RAG", "embeddings", "vector DB", "LangChain", "LangGraph", "agents", "tool calling", "memory", "evaluation", "observability", "Ollama", "OpenAI API"].map((name) => ({ name, track: "llm_agentic_ai", status: "planned" }))
  ]
};

export const gymRoutine = [
  ["Monday", "Push day - chest, shoulders, triceps"],
  ["Tuesday", "Pull day - back, biceps"],
  ["Wednesday", "Legs + core"],
  ["Thursday", "Upper body mixed"],
  ["Friday", "Full body + conditioning"],
  ["Saturday", "Rest or light walk"],
  ["Sunday", "Rest or light walk"]
];

export const exams = [
  ["CAT 2026", ["VARC", "LRDI", "Quant"]],
  ["GATE DA", ["probability/statistics", "linear algebra", "calculus/optimization", "programming/DSA", "DBMS/warehousing", "ML", "AI"]],
  ["GATE Mechanical", ["engineering mathematics", "applied mechanics/design", "fluids/thermal", "materials/manufacturing/industrial"]],
  ["IIT JAM Maths", ["real analysis", "multivariable calculus", "differential equations", "linear algebra", "algebra/groups"]],
  ["IIT JAM Physics", ["mathematical methods", "mechanics", "optics/waves", "electricity/magnetism", "thermodynamics", "modern physics", "solid state/electronics"]]
];
