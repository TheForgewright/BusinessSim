# Business Simulation Game

A comprehensive web-based business simulation and economic game designed for classroom use where students manage companies, invest in stocks, and compete for the highest final score over a predetermined number of turns.

## 🎮 Game Overview

Students manage companies in a competitive economic environment, making strategic decisions about:
- **Facility Management** (physical & personnel)
- **Capital Generation** (Goods, IP, Influence, Labor, Cash)
- **Stock Market Trading**
- **Debt Management** with interest and auto-pay
- **Product Creation** with market positioning tags
- **Market Competition** based on product overlap and saturation

**Winning Condition**: Highest score (Company Equity + Personal Cash) at game end

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Seed Database

```bash
python seed_data.py
```

This creates:
- 7 facility templates (R&D Lab, Sales Team, Warehouse, etc.)
- 15 product tags (Consumer, Enterprise, Technology, etc.)
- Demo professor account: `professor / password`
- Demo student account: `student / password`
- Demo game ready to play

### 3. Run Server

```bash
python run.py
```

Server starts at: **http://localhost:5000**

---

## 📚 Core Game Mechanics

### Capital System

**5 Types of Capital**:
- **Goods**: Physical materials, inventory
- **IP**: Patents, designs, research, proprietary technology
- **Influence**: Brand recognition, market position, relationships
- **Labor**: Skilled workforce, training, human capital
- **Cash**: Currency

Each capital type has **Active** and **Backed-up** storage with different storage costs.

### Facility System

**Two Facility Types**:

1. **Physical** (buildings, equipment)
   - Shutdown depreciation: 1× normal rate
   - Examples: R&D Lab, Warehouse, Factory Floor

2. **Personnel** (workforce, teams)
   - Shutdown depreciation: **4× rate** (staff leaves!)
   - Examples: R&D Staff, Sales Team, Marketing Department

**Facility Mechanics**:
- Weekly generation of capital based on dice rolls
- Focus bonus (company chooses one capital type to boost)
- Depreciation based on condition (100% → 0%)
- Periodic maintenance required
- Efficiency thresholds affect generation

### Weekly Turn Processing (29 Phases)

Each week, the game processes:

1. **Phase 1-4**: Track equity, increment week, reset trading, clean history
2. **Phase 5-7**: Facility depreciation, operating costs, efficiency checks
3. **Phase 8-9**: Capital generation rolls, storage costs
4. **Phase 10**: Maintenance checks
5. **Phase 11-14**: Debt interest, compounding, auto-pay, due dates
6. **Phase 15-17**: Treasury update, construction plans, completions
7. **Phase 18**: Capital attrition (decay if not generated)
8. **Phase 19-21**: Stock transactions, price updates, dividends
9. **Phase 22-24**: Scheduled events, multi-week events, professor-triggered
10. **Phase 25-27**: Market demand, product saturation, degradation
11. **Phase 28-29**: Status effects, UI refresh

### Debt Management

**Loan Features**:
- Annual interest rates
- Multiple compounding frequencies (daily, weekly, monthly, quarterly, or none)
- Auto-pay system (respects cash reserves)
- Due dates with default handling
- Creditor tracking and collateral

**Debt Payment Priority**:
1. Accrued interest paid first
2. Then principal
3. Auto-pay processes BEFORE earnings added to treasury

### Stock Market

**Dynamic Stock Pricing**:
```
Stock Price = (Base Equity / Total Shares) × (1 + Dividend Modifier + Momentum Bonus)

Base Equity = (Capital Value + Cash - Total Debt)
```

**Trading**:
- Buy/sell at current price
- Optional weekly trading limits (professor configurable)
- Dividends paid to all shareholders
- Stock dilution through issuing new shares

### Product Tagging & Market Positioning

**Product Creation**:
- Invest IP + Goods capital to create products
- Must assign exactly **3 tags** (e.g., "Consumer + Technology + Mobile")
- Tags define market positioning:
  - **Demand Multiplier**: Volume potential (higher = more sales)
  - **Profit Margin**: Margin per sale (higher = better margins)

**Market Competition**:
- Products compete based on tag overlap
- Share 3 tags = **Full competition** (100% saturation weight)
- Share 2 tags = **Partial competition** (50% saturation weight)
- Share 0-1 tags = No competition

**Strategic Archetypes**:
1. **Volume Play** (e.g., Consumer + Budget + Standard)
   - High demand, low margins
   - Requires efficient operations and multiple sales teams

2. **Margin Play** (e.g., Luxury + Premium + AI)
   - Low demand, high margins
   - Smaller market, defend niche aggressively

3. **Balanced** (e.g., Technology + Standard + Software)
   - Moderate demand and margins
   - Reliable, predictable growth

---

## 🎓 Professor Controls

Professors have full control over:

**Game Settings**:
- Total weeks (e.g., 50, 100)
- Max turn advancement (e.g., students can advance 3 weeks at once)
- Starting capital for new companies
- Depreciation rates
- Maintenance frequency and costs
- Storage costs

**Time Control**:
- Advance game by N weeks
- Pause/resume game
- Set turn limits

**Event System**:
- Create scheduled events (trigger at specific weeks)
- Create instant events (immediate effects)
- Create multi-week events (ongoing effects)
- Target specific companies or all companies
- Target specific product tags

**Configuration**:
- Add/modify facility templates
- Create/manage product tags
- Adjust economic settings (saturation rates, degradation, etc.)
- View all company data

---

## 👨‍💼 Student Features

**Company Management**:
- View capital inventory (active vs backed-up)
- Set weekly focus (boost one capital type)
- Build facilities (from templates)
- Shutdown/activate facilities
- Manage debts (take loans, pay manually)
- Transfer capital between active/backed-up

**Products & Sales**:
- Create products from capital
- Assign 3 market positioning tags
- Link products to sales facilities
- View market saturation and competition

**Stock Trading**:
- Buy/sell stock in other companies
- View portfolio
- Track personal wealth (cash + portfolio value)

**Financial Dashboard**:
- Company cash and equity
- Stock price
- Total debt
- Facility conditions
- Capital inventory

---

## 🏗️ Project Structure

```
BusinessSim/
├── app/
│   ├── models/           # Database models
│   │   └── models.py     # Game, Company, Facility, Debt, Product, etc.
│   ├── routes/           # Flask blueprints
│   │   ├── main.py       # Home, about, logout
│   │   ├── professor.py  # Professor dashboard and controls
│   │   ├── student.py    # Student dashboard
│   │   ├── auth.py       # Login/register
│   │   └── api.py        # JSON API endpoints
│   ├── game_engine/      # Core game logic
│   │   ├── turn_processor.py       # 29-phase weekly turn
│   │   ├── capital_generation.py   # Facility generation
│   │   ├── facility_management.py  # Depreciation, maintenance
│   │   ├── debt_management.py      # Interest, auto-pay
│   │   ├── stock_market.py         # Stock pricing, trading
│   │   ├── product_management.py   # Products, tags, saturation
│   │   └── dice.py                 # Dice rolling utilities
│   ├── static/
│   │   ├── css/          # Custom styles
│   │   └── js/           # JavaScript (AJAX, UI helpers)
│   ├── templates/        # HTML templates
│   │   ├── base.html
│   │   ├── student/      # Student dashboard pages
│   │   ├── professor/    # Professor dashboard pages
│   │   └── auth/         # Login/register
│   └── __init__.py       # Flask app factory
├── data/                 # SQLite database
│   └── business_sim.db
├── config.py             # Game configuration
├── run.py                # Server entry point
├── seed_data.py          # Database seeding script
└── requirements.txt      # Python dependencies
```

---

## 🔧 Technology Stack

- **Backend**: Python 3.11, Flask 3.0
- **Database**: SQLite (via SQLAlchemy)
- **Frontend**: HTML/CSS/JavaScript (Bootstrap 5.3)
- **Architecture**: REST API + Server-side rendering

---

## 📖 Example Gameplay

**Week 0** (Game Start):
1. Student creates company "Tech Innovations Inc."
2. Receives $5,000 Cash, 1,000 shares (100% ownership)
3. Builds "R&D Lab" and "R&D Staff" facilities (cost: Capital + Cash)

**Week 1-5**:
1. Set weekly focus to "IP"
2. R&D facilities generate IP each week (d8+3 base + 5 focus bonus)
3. Pay operating costs and storage costs
4. IP accumulates in active inventory

**Week 6**:
1. Create product "Cloud AI Platform"
2. Tags: Technology + Cloud + AI
3. Invest 50 IP + 30 Goods
4. Product value: 80, demand: 1.0×, margin: 1.43×

**Week 7-10**:
1. Build "Sales Team" facility
2. Link "Cloud AI Platform" to Sales Team
3. Sales Team generates revenue based on product value, tags, and saturation
4. Revenue added to company cash

**Week 11**:
1. Company equity increases
2. Stock price rises
3. Student sells 200 shares to personal account for cash
4. Uses personal cash to buy stock in competitor companies

**Week 15**:
1. Market event triggers: "AI Boom - All AI products +30% demand"
2. "Cloud AI Platform" revenue increases significantly
3. Student takes $10,000 loan to build more facilities faster

**Week 50** (Game End):
- Final Score = Company Equity + Personal Cash
- Student with highest score wins!

---

## 🎯 Learning Objectives

This simulation teaches:

1. **Business Operations**
   - Capital management
   - Facility depreciation and maintenance
   - Operating costs vs revenue

2. **Financial Management**
   - Debt management (interest, compounding)
   - Cash flow planning
   - Investment decisions

3. **Market Economics**
   - Supply and demand
   - Market saturation
   - Product differentiation
   - Competition dynamics

4. **Strategic Thinking**
   - Volume vs margin strategies
   - Market positioning
   - Risk management
   - Long-term planning

5. **Stock Market Fundamentals**
   - Equity valuation
   - Stock pricing dynamics
   - Portfolio management
   - Dividends and ownership

---

## 🛠️ Development

### Adding New Facility Templates

Edit `seed_data.py` and add to the `templates` list:

```python
{
    'name': 'Server Farm',
    'facility_type': 'physical',
    'description': 'Cloud infrastructure for SaaS products',
    'build_cost': {'Goods': 200, 'IP': 100, 'Cash': 1000},
    'build_time_weeks': 20,
    'weekly_operating_cost': 300.0,
    'cost_per_capital': {'IP': 20, 'Cash': 5},
    'base_generation': {'IP': 'd10+6', 'Cash': 'd12+8'},
    'focus_bonuses': {'IP': 8, 'Cash': 4},
    'link_capacity': 0
}
```

### Adding New Tags

Edit `seed_data.py` and add to the `tags` list:

```python
{
    'name': 'Gaming',
    'demand': 1.8,
    'margin': 0.9,
    'description': 'Gaming products - high volume, competitive'
}
```

### Customizing Game Settings

Edit `config.py`:

```python
class Config:
    GAME_TOTAL_WEEKS = 100  # Change game length
    BASE_DEPRECIATION_RATE = 3.0  # Faster depreciation
    MARKET_SATURATION_RATE = 0.5  # Higher saturation penalty
    # ... etc
```

---

## 📝 API Endpoints

### Stock Trading
- `POST /api/stock/buy` - Buy stock
- `POST /api/stock/sell` - Sell stock

### Debt Management
- `POST /api/debt/create` - Take out loan
- `POST /api/debt/<id>/pay` - Make manual payment

### Products
- `POST /api/product/create` - Create product from capital

### Facilities
- `POST /api/facility/<id>/shutdown` - Shutdown facility
- `POST /api/facility/<id>/activate` - Activate facility

### Capital
- `POST /api/company/<id>/capital/transfer` - Transfer active ↔ backed-up

### Data
- `GET /api/company/<id>/data` - Get company data
- `GET /api/game/<id>/tags` - Get all tags for game
- `GET /api/player/wealth` - Get player's total wealth

---

## 🐛 Known Limitations

Current version is a **functional prototype** with these limitations:

1. **Basic UI**: Functional but not polished
2. **Limited Events**: Event system is basic (effects not fully implemented)
3. **No Facility Building UI**: Students must use seed data facilities
4. **No Product Revenue**: Sales facilities don't calculate revenue yet (calculation logic exists)
5. **No Capital Attrition**: 7-week decay not implemented
6. **No Construction Timers**: Facilities built instantly
7. **Simple Auth**: Password hashing but no email verification, etc.

**Future Enhancements**:
- Facility marketplace (build from template)
- Product revenue generation
- Event effects implementation
- Construction queues
- Advanced charts and analytics
- Multi-game support for students
- Historical data and reports
- Export game results to CSV

---

## 📄 License

This project is for educational purposes.

---

## 🙏 Credits

Designed for business/economics classroom use. Implements comprehensive economic simulation mechanics including:
- 29-phase weekly turn processing
- Differential depreciation (physical vs personnel)
- Debt management with compounding
- Product tagging and market saturation
- Stock market dynamics

Built with Flask, SQLAlchemy, and Bootstrap.

---

## 💡 Support

For issues or questions:
- Check the design document for detailed mechanics
- Review `seed_data.py` for examples
- Examine `game_engine/` modules for game logic
- See `routes/` for API endpoints

**Demo Accounts**:
- Professor: `professor / password`
- Student: `student / password`

Happy simulating! 🎮📈
