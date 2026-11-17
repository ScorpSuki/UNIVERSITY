import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

# ========== НҰСҚА 4 ПАРАМЕТРЛЕРІ ==========
Ko, T1, T2 = 1.2, 1.0, 0.3            # объект
Kp, Ti, Td = 3.5, 0.9, 0.2             # реттегіш

print("=" * 60)
print("НҰСҚА 4")
print(f"K_об={Ko}, T1={T1} с, T2={T2} с")
print(f"K_р={Kp}, T_и={Ti} с, T_д={Td} с")
print("=" * 60)

# Объект
plant_num = [Ko]
plant_den = np.polymul([T1, 1], [T2, 1])
print("\nОбъект W_об(s):")
print(f"  Алым:  {plant_num}")
print(f"  Бөлім: {plant_den}")

# Реттегіштер (алым, бөлім)
controllers = {
    'П':   ([Kp], [1]),
    'И':   ([1], [Ti, 0]),
    'ПИ':  ([Kp*Ti, Kp], [Ti, 0]),
    'ПД':  ([Kp*Td, Kp], [1]),
    'ПИД': ([Kp*Ti*Td, Kp*Ti, Kp], [Ti, 0]),
}

print("\nРеттегіштердің беріліс функциялары:")
for name, (cn, cd) in controllers.items():
    print(f"  {name}:  W_р(s) = {cn} / {cd}")

# ========== ТҰЙЫҚ ЖҮЙЕЛЕРДІ ЕСЕПТЕУ ==========
t = np.linspace(0, 120, 12001)
results = {}

print("\n" + "=" * 60)
print("ТҰЙЫҚ ЖҮЙЕЛЕРДІҢ АНАЛИЗІ")
print("=" * 60)

for name, (cn, cd) in controllers.items():
    num = np.polymul(cn, plant_num)          # W_р · W_об алымы
    den_open = np.polymul(cd, plant_den)     # W_р · W_об бөлімі
    den = np.polyadd(den_open, num)          # 1 + W_рW_об
    roots = np.roots(den)
    stable = np.max(np.real(roots)) < 0

    t_out, h = signal.step(signal.lti(num, den), T=t)

    h_inf = num[-1] / den[-1]
    e_st = (1 - h_inf) * 100
    sigma = max(0.0, (np.max(h) - h_inf) / h_inf * 100) if h_inf != 0 else 0.0

    # Реттеу уақыты (5 % жолақ)
    band = 0.05 * abs(h_inf)
    out = np.where(np.abs(h - h_inf) > band)[0]
    t_p = t_out[out[-1]] if len(out) > 0 else 0.0

    results[name] = {
        'h': h, 'stable': stable, 'num': num, 'den': den,
        'roots': roots, 'h_inf': h_inf, 'e_st': e_st,
        'sigma': sigma, 't_p': t_p
    }

    print(f"\n{name}-реттегіш:")
    print(f"  Тұйық жүйе алымы:  {np.round(num, 5)}")
    print(f"  Тұйық жүйе бөлімі: {np.round(den, 5)}")
    print(f"  Полюстер: {np.round(roots, 4)}")
    print(f"  Орнықты: {stable}")
    print(f"  h∞ = {h_inf:.6f}   e_ст = {e_st:.2f}%   σ = {sigma:.1f}%   t_р = {t_p:.2f} с")

# П-реттегішті формуламен тексеру
e_formula = 1 / (1 + Kp * Ko) * 100
print(f"\nП-реттегіш үшін формула: e_ст = 1/(1+K_р·K_об)·100% = {e_formula:.2f}%")

# ========== НӘТИЖЕ КЕСТЕСІ ==========
print("\n" + "=" * 60)
print("НӘТИЖЕЛЕР КЕСТЕСІ")
print("=" * 60)
print(f"{'Реттегіш':<8} {'Орнықты':<10} {'e_ст, %':<10} {'σ, %':<10} {'t_р, с':<10}")
print("-" * 48)
for name in ['П', 'И', 'ПИ', 'ПД', 'ПИД']:
    r = results[name]
    print(f"{name:<8} {str(r['stable']):<10} {r['e_st']:<10.2f} {r['sigma']:<10.1f} {r['t_p']:<10.2f}")

# Ең жақсы реттегіш
candidates = [(n, results[n]['t_p']) for n in results 
              if results[n]['e_st'] < 0.1 and results[n]['sigma'] <= 30]
best = min(candidates, key=lambda x: x[1])
print(f"\nЕң жақсы реттегіш (e_ст≈0 және σ≤30%): {best[0]} (t_р = {best[1]:.2f} с)")

# ========== ГРАФИК ==========
plt.figure(figsize=(10, 6))
for name in ['П', 'И', 'ПИ', 'ПД', 'ПИД']:
    plt.plot(t, results[name]['h'], label=name, linewidth=1.7)
plt.axhline(1, color='k', ls='--', alpha=0.5, label='Қажетті мән')
plt.xlim(0, 12)
plt.ylim(0, 1.55)
plt.xlabel('t, с')
plt.ylabel('h(t)')
plt.title('Нұсқа 4: Тұйық жүйелердің өтпелі функциялары')
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig('variant4_step_responses.png', dpi=150)
plt.show()