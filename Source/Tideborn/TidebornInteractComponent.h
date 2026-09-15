#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "TidebornInteractComponent.generated.h"

class UInputAction;
struct FInputActionValue;

UCLASS(ClassGroup=(Tideborn), meta=(BlueprintSpawnableComponent))
class TIDEBORN_API UTidebornInteractComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UTidebornInteractComponent();

protected:
	virtual void BeginPlay() override;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Tideborn|Input")
	TObjectPtr<UInputAction> InteractAction;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Tideborn|Interaction")
	float InteractDistance = 250.f;

	void BindInput();
	void OnInteract(const FInputActionValue& Value);
	void TryInteract();

	bool bInputBound = false;
};
