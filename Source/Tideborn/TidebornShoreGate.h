#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "TidebornShoreGate.generated.h"

class UBoxComponent;
class UStaticMeshComponent;

UCLASS()
class TIDEBORN_API ATidebornShoreGate : public AActor
{
	GENERATED_BODY()

public:
	ATidebornShoreGate();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
	TObjectPtr<UBoxComponent> BlockVolume;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
	TObjectPtr<UStaticMeshComponent> GateMesh;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Tideborn|Gate")
	float CompanionCheckRadius = 700.f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Tideborn|Gate")
	bool bOpen = false;

private:
	bool HasTamedCompanionNearPlayer() const;
	void SetGateOpen(bool bShouldOpen);
};
