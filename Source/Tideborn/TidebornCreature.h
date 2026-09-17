#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "TidebornInteractable.h"
#include "TidebornCreature.generated.h"

class UStaticMeshComponent;

UENUM(BlueprintType)
enum class ETidebornCreatureRole : uint8
{
	Threat,
	Tameable
};

UCLASS()
class TIDEBORN_API ATidebornCreature : public ACharacter, public ITidebornInteractable
{
	GENERATED_BODY()

public:
	ATidebornCreature();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Tideborn|Creature")
	ETidebornCreatureRole CreatureRole = ETidebornCreatureRole::Threat;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Tideborn|Creature")
	FName DisplayName = FName(TEXT("Creature"));

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Tideborn|Creature")
	float MaxHealth = 50.f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Tideborn|Creature")
	float Health = 50.f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Tideborn|Creature")
	bool bTamed = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Tideborn|Creature")
	float AggroRadius = 900.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Tideborn|Creature")
	float AttackRange = 120.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Tideborn|Creature")
	float AttackDamage = 8.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Tideborn|Creature")
	float AttackCooldown = 1.2f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Tideborn|Tame")
	FName BaitItemId = FName(TEXT("KelpBait"));

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Tideborn|Tame")
	int32 FeedsNeededToTame = 3;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Tideborn|Tame")
	int32 FeedsReceived = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Tideborn|Tame")
	float FollowDistance = 280.f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Tideborn|Creature")
	TObjectPtr<UStaticMeshComponent> BodyMesh;

	virtual bool Tideborn_TryInteract(AActor* Interactor) override;

	UFUNCTION(BlueprintCallable, Category="Tideborn|Creature")
	void ApplyDamageFromPlayer(float Amount);

protected:
	float AttackCooldownLeft = 0.f;

	APawn* FindPlayerPawn() const;
	void TickThreat(float DeltaSeconds);
	void TickFollow(float DeltaSeconds);
	bool TryFeed(AActor* Interactor);
};
